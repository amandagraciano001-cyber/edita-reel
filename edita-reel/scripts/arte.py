"""Põe a arte por cima do reel: capa grande, título no alto, legenda com a palavra ativa, prints flutuando,
listas acendendo, números e o fecho. Tudo numa camada só, quadro a quadro, sobreposta uma vez no vídeo.

Uso:
    python arte.py VIDEO PASTA ARTE.json [--velocidade 1.0] [--saida ARQUIVO]

VIDEO é o reel já cortado (montar.py) e, se quiser, com ritmo (ritmo.py). Sem legenda queimada: a legenda
entra aqui. PASTA é a pasta edita-reel/ do vídeo. --velocidade é a mesma do montar.py.
Vídeo HDR do iPhone continua HDR. Grava PASTA/reel-final.mp4 (ou --saida).

ARTE.json (tudo opcional; um tempo é número em segundos ou {"palavra": "x", "n": 1, "mais": 0.5}):
{
  "titulo": "Isso tem um nome",
  "capa": {"texto": "Não é preguiça. É medo", "ate": null, "y": 1000, "tam": 130},
  "legenda": "ativa",                         "ativa" (palavra falada em destaque) ou "nenhuma"
  "legenda_y": 1400, "maximo": 4, "correcoes": {"ia": "IA"},
  "inserts": [{"imagem": "prints/site.png", "recorte": [0, 120, 740, 880], "de": {"palavra": "site"}, "ate": {"palavra": "site", "mais": 3},
               "x": 260, "y": 690, "largura": 560, "girar": 2, "credito": "site.com"}],
  "listas": [{"itens": ["Letramento", "Adestramento"], "de": 4.0, "ate": 9.0, "marcos": [4.0, 6.5], "x": 70, "y": 1110, "tam": 62, "passo": 92}],
  "numeros": [{"numero": "27", "rotulo": "coisas", "de": 1.0, "ate": 4.0}],
  "fecho": {"texto": "Comenta PALAVRA", "ultimos_s": 1.8}      ou {"url": "seusite.com", "rotulo": "o link"} pro TikTok
}
"""
import argparse
import sys
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image

import estilo as E
from comum import (FPS, codificador, duracao, eh_hdr, fim_da_primeira_frase, palavras_no_reel, resolver_tempo)
from montar import para_hlg, salvar_png16


# ------------------------------------------------------------ eventos: (ini, fim, chave(t_rel), imagem(t_rel))
def fixo(im):
    return (lambda t: 0), (lambda t: im)


def legenda_ativa(palavras, maximo=4, y=1400, tam=50, correcoes=None):
    corr = correcoes or {}

    def limpa(w):
        nu = w.strip().strip(",.?!")
        pont = "".join(c for c in w.strip() if c in ",.?!")
        return corr.get(nu, nu) + pont
    frases, atual = [], []
    for w in palavras:
        atual.append(w)
        if len(atual) >= maximo or limpa(w[0]).endswith((".", "?", "!", ",", ":")):
            frases.append(atual)
            atual = []
    if atual:
        frases.append(atual)
    ev = []
    for fr in frases:
        txts = [limpa(w[0]) for w in fr]
        for i, (w, a, b) in enumerate(fr):
            fim = fr[i + 1][1] if i + 1 < len(fr) else b + 0.15
            ev.append([a, max(fim, a + 0.05), *fixo(E.legenda_ativa(txts, i, y=y, tam=tam))])
    ev.sort(key=lambda e: e[0])
    for k in range(len(ev) - 1):           # palavras do Whisper às vezes se encavalam
        ev[k][1] = min(ev[k][1], ev[k + 1][0])
    return [tuple(e) for e in ev]


def insert_flutuante(img, x, y, larg, girar=0, credito=None, entra=0.25):
    """Print flutuando com entrada suave: cresce de 92% a 100% nos primeiros `entra` segundos."""
    n = max(int(entra * FPS), 1)
    cache = {}

    def passo(t):
        return min(int(t * FPS), n)

    def imagem(t):
        k = passo(t)
        if k not in cache:
            e = 0.92 + 0.08 * k / n
            l = int(larg * e)
            cache[k] = E.flutuante(img, x + (larg - l) / 2, y + (larg - l) / 2, l, girar=girar, rotulo=credito if k == n else None)
        return cache[k]
    return passo, imagem


def lista_acende(itens, marcos_rel, **kw):
    cache = {}

    def passo(t):
        return sum(1 for m in marcos_rel if t >= m)

    def imagem(t):
        k = passo(t)
        if k not in cache:
            cache[k] = E.lista_topo(itens, k, **kw)
        return cache[k]
    return passo, imagem


def montar_eventos(arte, palavras, total, pasta_arte):
    ev = []
    f1 = fim_da_primeira_frase(palavras)
    if arte.get("capa"):
        c = arte["capa"]
        ate = resolver_tempo(c.get("ate"), palavras, f1)
        ev.append((0.0, ate, *fixo(E.capa_grande(c["texto"], y0=c.get("y", 1000), tam=c.get("tam", 130)))))
        ini_titulo = ate
    else:
        ini_titulo = 0.0
    if arte.get("titulo"):
        ev.append((ini_titulo, total, *fixo(E.titulo_topo(arte["titulo"], y=arte.get("titulo_y", 130), tam=arte.get("titulo_tam", 30)))))
    if arte.get("legenda", "ativa") == "ativa":
        ev += legenda_ativa(palavras, arte.get("maximo", 4), arte.get("legenda_y", 1400), arte.get("legenda_tam", 50), arte.get("correcoes"))
    for ins in arte.get("inserts", []):
        caminho = ins["imagem"] if os.path.isabs(ins["imagem"]) else os.path.join(pasta_arte, ins["imagem"])
        img = Image.open(caminho)
        if ins.get("recorte"):
            img = img.crop(tuple(ins["recorte"]))
        de, ate = resolver_tempo(ins["de"], palavras), resolver_tempo(ins["ate"], palavras)
        ev.append((de, ate, *insert_flutuante(img, ins.get("x", 160), ins.get("y", 700), ins.get("largura", 760),
                                              ins.get("girar", 0), ins.get("credito"))))
    for li in arte.get("listas", []):
        de, ate = resolver_tempo(li["de"], palavras), resolver_tempo(li["ate"], palavras)
        marcos = [resolver_tempo(m, palavras) - de for m in li.get("marcos", [])] or [0.0]
        kw = {k: li[k] for k in ("x", "y", "tam", "passo") if k in li}
        ev.append((de, ate, *lista_acende(li["itens"], marcos, **kw)))
    for nu in arte.get("numeros", []):
        de, ate = resolver_tempo(nu["de"], palavras), resolver_tempo(nu["ate"], palavras)
        ev.append((de, ate, *fixo(E.numero_flutuante(nu["numero"], nu.get("rotulo", ""), nu.get("x", 90), nu.get("y", 330), nu.get("tam", 260)))))
    if arte.get("fecho"):
        f = arte["fecho"]
        ini = max(total - f.get("ultimos_s", 1.8), 0)
        im = E.selo_url(f.get("rotulo", "o link"), f["url"], y=f.get("y", 1260)) if f.get("url") else E.titulo_topo(f["texto"], y=f.get("y", 1300), tam=f.get("tam", 34))
        ev.append((ini, total + 1, *fixo(im)))
    return ev


# ------------------------------------------------------------ render: uma camada, só os quadros que mudam
def compor(video, eventos, saida, hdr):
    total = duracao(video)
    n = int(total * FPS) + 1
    tmp = tempfile.mkdtemp(prefix="arte-")
    try:
        quadros, chave_ant, seq = {}, None, []
        for k in range(n):
            t = k / FPS
            ativos = [(i, ch(t - ini)) for i, (ini, fim, ch, _) in enumerate(eventos) if ini <= t < fim]
            chave = tuple(ativos)
            if chave != chave_ant:
                if chave not in quadros:
                    q = E.base()
                    for i, _ in ativos:
                        q.alpha_composite(eventos[i][3](t - eventos[i][0]))
                    p = os.path.join(tmp, f"q{len(quadros):05d}.png")
                    salvar_png16(p, para_hlg(q)) if hdr else q.save(p, compress_level=1)
                    quadros[chave] = p
                seq.append((quadros[chave], t))
                chave_ant = chave
        lista = os.path.join(tmp, "lista.txt")
        with open(lista, "w", encoding="utf-8") as f:
            for i, (p, t) in enumerate(seq):
                fim = seq[i + 1][1] if i + 1 < len(seq) else total
                f.write(f"file '{p}'\nduration {max(fim - t, 1 / FPS):.5f}\n")
            f.write(f"file '{seq[-1][0]}'\n")
        trilha = os.path.join(tmp, "arte.mov")
        codec = ["-c:v", "png", "-pix_fmt", "rgba64be"] if hdr else ["-c:v", "qtrle", "-pix_fmt", "argb"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-vf", f"fps={FPS}", *codec,
                        "-t", f"{total:.3f}", trilha], check=True)
        if hdr:
            fc = "[1:v]format=rgba64le[l];[0:v][l]overlay=0:0:format=yuv444p10:eof_action=pass,format=yuv420p10le[v]"
        else:
            fc = "[1:v]format=rgba[l];[0:v][l]overlay=0:0:format=yuv420:eof_action=pass,format=yuv420p[v]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", trilha, "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                        *codificador(hdr), "-c:a", "copy", "-movflags", "+faststart", saida], check=True)
        return len(quadros)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("pasta")
    ap.add_argument("arte")
    ap.add_argument("--velocidade", type=float, default=1.0)
    ap.add_argument("--saida")
    a = ap.parse_args()
    arte = json.load(open(a.arte, encoding="utf-8"))
    palavras = palavras_no_reel(a.pasta, a.velocidade)
    total = duracao(a.video)
    hdr = eh_hdr(a.video)
    eventos = montar_eventos(arte, palavras, total, os.path.dirname(os.path.abspath(a.arte)))
    saida = a.saida or os.path.join(a.pasta, "reel-final.mp4")
    n = compor(a.video, eventos, saida, hdr)
    print(f"Pronto: {saida}  ({total:.1f}s, {'HDR' if hdr else 'SDR'}, {len(eventos)} eventos, {n} quadros de arte)")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
