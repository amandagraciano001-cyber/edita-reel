"""Peças comuns aos scripts: tempo das palavras no reel cortado, codificador certo (HDR ou SDR), duração.

Não roda sozinho. Os outros scripts importam daqui.
"""
import json
import os
import subprocess
import unicodedata

from montar import probe  # noqa: F401  (reexportado)

FPS = 30
W, H = 1080, 1920


def duracao(video):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                                capture_output=True, text=True).stdout)


def codificador(hdr, crf=18):
    """Parâmetros do ffmpeg que mantêm a cor: HLG em 10 bits (iPhone) ou H.264 8 bits (SDR)."""
    if hdr:
        return ["-c:v", "libx265", "-crf", str(crf), "-preset", "fast", "-pix_fmt", "yuv420p10le", "-maxrate", "8M", "-bufsize", "16M",
                "-x265-params", "colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc:log-level=error",
                "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-tag:v", "hvc1"]
    return ["-c:v", "libx264", "-crf", str(crf + 1), "-preset", "fast", "-pix_fmt", "yuv420p", "-maxrate", "6M", "-bufsize", "12M"]


def eh_hdr(video):
    return probe(video)["hdr"]


# ------------------------------------------------------------ palavras no tempo do reel já cortado
def carregar(pasta):
    edl = [b for b in json.load(open(os.path.join(pasta, "edl.json"))) if b.get("manter", True)]
    pal = json.load(open(os.path.join(pasta, "palavras.json")))
    return edl, pal


def palavras_no_reel(pasta, velocidade=1.0):
    """Lista de (palavra, início, fim) no tempo do reel cortado e acelerado, na ordem dos blocos do edl.

    Cada palavra entra uma vez só, pelo meio dela, no bloco que a contém. Blocos reordenados no edl
    (abertura fria, por exemplo) reordenam as palavras junto.
    """
    edl, pal = carregar(pasta)
    out, off = [], 0.0
    for b in edl:
        for p in pal:
            meio = (p["s"] + p["e"]) / 2
            if b["ini"] - 0.01 <= meio <= b["fim"] + 0.01:
                a = (off + max(p["s"] - b["ini"], 0)) / velocidade
                e = (off + min(p["e"] - b["ini"], b["fim"] - b["ini"])) / velocidade
                out.append((p["w"], round(a, 3), round(e, 3)))
        off += b["fim"] - b["ini"]
    return out


def _norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if c.isalnum() and not unicodedata.combining(c))


def t_palavra(palavras, alvo, n=1, depois=0.0):
    """Instante em que a n-ésima ocorrência de `alvo` começa (depois de `depois` s). Compara sem acento e sem pontuação."""
    k = 0
    for w, a, b in palavras:
        if a >= depois and _norm(w).startswith(_norm(alvo)):
            k += 1
            if k == n:
                return a
    raise SystemExit(f"Palavra não encontrada na transcrição: {alvo!r} (ocorrência {n})")


def blocos_de_fala(palavras, pausa=0.35):
    """Trechos (início, fim) de fala contínua, separados por silêncios maiores que `pausa`."""
    bl = []
    for w, a, b in palavras:
        if bl and a - bl[-1][1] <= pausa:
            bl[-1][1] = b
        else:
            bl.append([a, b])
    return [(a, b) for a, b in bl]


def blocos_do_reel(pasta, velocidade=1.0, pausa=0.35):
    """Os pontos naturais de corte do reel já cortado: cada bloco do edl (uma frase) e, dentro dele, cada pausa
    maior que `pausa`. Devolve (início, fim) no tempo do reel. Num reel cortado por cortes.py as pausas longas
    já saíram, então o que manda são as fronteiras dos blocos."""
    edl, pal = carregar(pasta)
    out, off = [], 0.0
    for b in edl:
        dentro = [(p["w"], (off + max(p["s"] - b["ini"], 0)) / velocidade, (off + min(p["e"] - b["ini"], b["fim"] - b["ini"])) / velocidade)
                  for p in pal if b["ini"] - 0.01 <= (p["s"] + p["e"]) / 2 <= b["fim"] + 0.01]
        ini_b, fim_b = off / velocidade, (off + b["fim"] - b["ini"]) / velocidade
        partes = blocos_de_fala(dentro, pausa) or [(ini_b, fim_b)]
        partes[0] = (ini_b, partes[0][1])
        partes[-1] = (partes[-1][0], fim_b)
        out += partes
        off += b["fim"] - b["ini"]
    return out


def fim_da_primeira_frase(palavras, padrao=2.5):
    for w, a, b in palavras:
        if w.strip().endswith((".", "?", "!")):
            return b
    return padrao


def resolver_tempo(valor, palavras, padrao=None):
    """Um tempo no arte.json pode ser número (segundos) ou {"palavra": "x", "n": 1, "mais": 0.5, "depois": 0}."""
    if valor is None:
        return padrao
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, dict) and "palavra" in valor:
        t = t_palavra(palavras, valor["palavra"], valor.get("n", 1), valor.get("depois", 0.0))
        return t + float(valor.get("mais", 0.0))
    raise SystemExit(f"Tempo inválido no arte.json: {valor!r}")
