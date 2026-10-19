"""Monta o reel: corta, enquadra em 9:16, queima a legenda, acelera e exporta.

Uso:
    python montar.py VIDEO PASTA [--velocidade 1.0] [--sem-legenda] [--sem-ingles]
                     [--formato 9:16|original] [--sem-audio] [--saida ARQUIVO]

Lê PASTA/edl.json (blocos com "manter") e, se existir, PASTA/legendas.json.
Grava PASTA/reel.mp4 (ou --saida).

Vídeo de iPhone em HDR (HLG) continua HDR: a legenda é convertida pro mesmo
espaço de cor, pra não sair lavada nem com o amarelo virando laranja.
--luz suave|forte clareia o rosto em vídeo SDR gravado com pouca luz (em HDR é ignorado,
pra não lavar a cor). --sem-legenda deixa o reel limpo pra arte.py colocar a legenda ativa.
Imagem e som são gerados em etapas separadas: juntos no mesmo filtro, o ffmpeg
pode congelar quadros.
"""
import argparse
import sys
import json
import os
import shutil
import struct
import subprocess
import tempfile
import zlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 30
AMARELO = (234, 219, 143, 255)   # legenda em português: amarelo claro em itálico
BRANCO = (255, 255, 255, 255)    # legenda em inglês
LUZ = {"suave": "eq=brightness=0.06:contrast=1.08:saturation=1.05,curves=master='0/0 0.25/0.32 0.6/0.7 1/1'",
       "forte": "eq=brightness=0.10:contrast=1.08:saturation=1.05,curves=master='0/0 0.25/0.34 0.6/0.72 1/1',colortemperature=temperature=5600"}
FONTES_ITALICO = ["/System/Library/Fonts/Supplemental/Arial Italic.ttf",
                  "/Library/Fonts/Arial Italic.ttf",
                  os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "ariali.ttf"),
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"]


def run(cmd):
    subprocess.run(cmd, check=True)


def probe(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,color_transfer:stream_side_data=rotation:format=duration",
                          "-of", "json", video], capture_output=True, text=True).stdout
    d = json.loads(out)
    st = d["streams"][0]
    w, h = st["width"], st["height"]
    rot = 0
    for sd in st.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    tem_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                                "stream=index", "-of", "csv=p=0", video],
                               capture_output=True, text=True).stdout.strip() != ""
    return {"w": w, "h": h, "hdr": st.get("color_transfer") == "arib-std-b67",
            "pq": st.get("color_transfer") == "smpte2084", "dur": float(d["format"]["duration"]),
            "audio": tem_audio}


def fonte(tam):
    for f in FONTES_ITALICO:
        if os.path.exists(f):
            return ImageFont.truetype(f, tam)
    return ImageFont.load_default()


# ------------------------------------------------------------ cor (HDR HLG)
def para_hlg(im):
    """Mantém o branco em sinal 1.0 e corrige só o gamut BT.709 -> BT.2020."""
    import numpy as np
    a_, b_, c_ = 0.17883277, 0.28466892, 0.55991073
    arr = np.asarray(im).astype(np.float64) / 255.0
    rgb, alpha = arr[..., :3], arr[..., 3:]
    lin = np.where(rgb <= 0.5, (rgb ** 2) / 3.0, (np.exp((np.clip(rgb, 0.5, 1) - c_) / a_) + b_) / 12.0)
    m = np.array([[0.6274, 0.3293, 0.0433], [0.0691, 0.9195, 0.0114], [0.0164, 0.0880, 0.8956]])
    e = np.clip(lin @ m.T, 0, None)
    sig = np.clip(np.where(e <= 1 / 12, 0.5 * np.sqrt(np.maximum(12 * e, 0)),
                           a_ * np.log(np.maximum(12 * e - b_, 1e-9)) + c_), 0, 1)
    return (np.concatenate([sig, alpha], -1) * 65535 + 0.5).astype(np.uint16)


def salvar_png16(caminho, arr):
    h, w = arr.shape[:2]
    be = arr.astype(">u2").tobytes()
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += be[y * w * 8:(y + 1) * w * 8]

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    open(caminho, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 6, 0, 0, 0))
                              + chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))


# ------------------------------------------------------------ legenda
def quadro_legenda(W, H, pt, en):
    k = W / 1080
    f1, f2 = fonte(int(46 * k)), fonte(int(37 * k))
    y1, y2 = int(H * 0.693), int(H * 0.725)
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not pt and not en:
        return base
    sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sombra)
    linhas = [(pt, f1, y1, AMARELO), (en, f2, y2, BRANCO)]
    for txt, f, y, _ in linhas:
        if txt:
            x = (W - d.textlength(txt, font=f)) / 2
            d.text((x + 2, y + 3), txt, font=f, fill=(0, 0, 0, 200), stroke_width=int(6 * k), stroke_fill=(0, 0, 0, 170))
    base.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(5 * k)))
    d = ImageDraw.Draw(base)
    for txt, f, y, cor in linhas:
        if txt:
            x = (W - d.textlength(txt, font=f)) / 2
            d.text((x, y), txt, font=f, fill=cor, stroke_width=max(2, int(3 * k)), stroke_fill=(0, 0, 0, 255))
    return base


def trilha_legenda(W, H, legendas, total, hdr, ingles, pasta):
    """Vídeo transparente com a legenda, um quadro por mudança de texto."""
    os.makedirs(pasta, exist_ok=True)
    seq, t, cache = [], 0.0, {}

    def img(pt, en):
        chave = (pt, en)
        if chave not in cache:
            p = os.path.join(pasta, f"l{len(cache):04d}.png")
            im = quadro_legenda(W, H, pt, en)
            salvar_png16(p, para_hlg(im)) if hdr else im.save(p)
            cache[chave] = p
        return cache[chave]
    for s in legendas:
        if s["ini"] > t:
            seq.append((img("", ""), s["ini"] - t))
            t = s["ini"]
        fim = min(s["fim"], total)
        if fim > t:
            seq.append((img(s["pt"], s.get("en", "") if ingles else ""), fim - t))
            t = fim
    if total > t:
        seq.append((img("", ""), total - t))
    lista = os.path.join(pasta, "lista.txt")
    with open(lista, "w", encoding="utf-8") as f:
        for p, d in seq:
            f.write(f"file '{p}'\nduration {d:.4f}\n")
        f.write(f"file '{seq[-1][0]}'\n")
    saida = os.path.join(pasta, "legenda.mov")
    codec = ["-c:v", "png", "-pix_fmt", "rgba64be"] if hdr else ["-c:v", "qtrle", "-pix_fmt", "argb"]
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista,
         "-vf", f"fps={FPS}", *codec, "-t", f"{total:.3f}", saida])
    return saida


# ------------------------------------------------------------ montagem
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("pasta")
    ap.add_argument("--velocidade", type=float, default=1.0)
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--sem-ingles", action="store_true")
    ap.add_argument("--sem-audio", action="store_true")
    ap.add_argument("--formato", default="9:16", choices=["9:16", "original"])
    ap.add_argument("--luz", choices=["suave", "forte"], help="clareia o rosto (só SDR)")
    ap.add_argument("--saida")
    a = ap.parse_args()

    info = probe(a.video)
    if info["pq"]:
        print("Aviso: vídeo em HDR PQ (não HLG). Vai sair em SDR e a cor pode mudar.")
    hdr = info["hdr"]
    W, H = (1080, 1920) if a.formato == "9:16" else (info["w"] // 2 * 2, info["h"] // 2 * 2)
    edl = [b for b in json.load(open(os.path.join(a.pasta, "edl.json"), encoding="utf-8")) if b.get("manter", True)]
    if not edl:
        raise SystemExit("Nenhum bloco marcado pra manter no edl.json.")
    total = sum(b["fim"] - b["ini"] for b in edl)
    saida = a.saida or os.path.join(a.pasta, "reel.mp4")
    tmp = tempfile.mkdtemp(prefix="edita-reel-")
    try:
        # 1. corte + enquadramento (imagem)
        enq = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
               if a.formato == "9:16" else f"scale={W}:{H}")
        if a.luz and not hdr:
            enq += "," + LUZ[a.luz]
        elif a.luz:
            print("Aviso: --luz é ignorado em vídeo HDR (a cor lavaria). Grave com mais luz ou use o SDR.")
        partes, rotulos = [], []
        for i, b in enumerate(edl):
            partes.append(f"[0:v]trim=start={b['ini']}:end={b['fim']},setpts=PTS-STARTPTS,{enq},fps={FPS},setsar=1[v{i}]")
            rotulos.append(f"[v{i}]")
        fc = ";".join(partes) + ";" + "".join(rotulos) + f"concat=n={len(edl)}:v=1:a=0[v]"
        if hdr:
            venc = ["-c:v", "libx265", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p10le", "-maxrate", "8M", "-bufsize", "16M",
                    "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:log-level=error",
                    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc"]
        else:
            venc = ["-c:v", "libx264", "-crf", "19", "-preset", "fast", "-pix_fmt", "yuv420p", "-maxrate", "6M", "-bufsize", "12M"]
        corte_v = os.path.join(tmp, "corte.mov")
        run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-filter_complex", fc, "-map", "[v]", "-an", *venc, corte_v])

        # 2. corte (som), com fade curtinho em cada emenda
        corte_a = None
        if info["audio"] and not a.sem_audio:
            partes, rotulos = [], []
            for i, b in enumerate(edl):
                d = b["fim"] - b["ini"]
                partes.append(f"[0:a]atrim=start={b['ini']}:end={b['fim']},asetpts=PTS-STARTPTS,"
                              f"afade=t=in:d=0.02,afade=t=out:st={max(d - 0.03, 0):.3f}:d=0.03[a{i}]")
                rotulos.append(f"[a{i}]")
            fc = ";".join(partes) + ";" + "".join(rotulos) + f"concat=n={len(edl)}:v=0:a=1[a]"
            corte_a = os.path.join(tmp, "corte.wav")
            run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-filter_complex", fc, "-map", "[a]", corte_a])

        # 3. legenda por cima
        video_final = corte_v
        leg_json = os.path.join(a.pasta, "legendas.json")
        if not a.sem_legenda and os.path.exists(leg_json):
            legendas = json.load(open(leg_json, encoding="utf-8"))
            trilha = trilha_legenda(W, H, legendas, total, hdr, not a.sem_ingles, os.path.join(tmp, "leg"))
            fmt = "yuv444p10" if hdr else "yuv420"
            saida_fmt = "yuv420p10le" if hdr else "yuv420p"
            video_final = os.path.join(tmp, "com-legenda.mov")
            run(["ffmpeg", "-v", "error", "-y", "-i", corte_v, "-i", trilha, "-filter_complex",
                 f"[1:v]format=rgba64le[l];[0:v][l]overlay=0:0:format={fmt}:eof_action=pass,format={saida_fmt}[v]",
                 "-map", "[v]", *venc, video_final])

        # 4. velocidade + junção final (imagem e som separados, depois juntos)
        v = a.velocidade
        vf = os.path.join(tmp, "v.mov")
        if abs(v - 1.0) > 1e-3:
            run(["ffmpeg", "-v", "error", "-y", "-i", video_final, "-vf", f"setpts=PTS/{v},fps={FPS}", "-an", *venc, vf])
        else:
            shutil.copy(video_final, vf)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", vf]
        if corte_a:
            af = os.path.join(tmp, "a.wav")
            filtro = (f"atempo={v}," if abs(v - 1.0) > 1e-3 else "") + "loudnorm=I=-14:TP=-1.5:LRA=9"
            run(["ffmpeg", "-v", "error", "-y", "-i", corte_a, "-af", filtro, "-ar", "48000", af])
            cmd += ["-i", af, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
        else:
            cmd += ["-map", "0:v"]
        tag = ["-tag:v", "hvc1"] if hdr else []
        run(cmd + ["-c:v", "copy", *tag, "-movflags", "+faststart", saida])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"Pronto: {saida}  ({total / a.velocidade:.1f}s, {'HDR' if hdr else 'SDR'}, {W}x{H})")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
