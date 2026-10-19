"""Monta o rascunho da legenda já no tempo do vídeo cortado.

Uso:
    python legendas.py PASTA [--max 32]

Lê PASTA/palavras.json e PASTA/edl.json e grava PASTA/legendas.json:
    [{"pt": "Eu sou boa numa coisa", "en": "", "ini": 0.12, "fim": 1.48}, ...]

Os tempos são do vídeo JÁ CORTADO (antes de acelerar). Depois de rodar:
corrija erros de transcrição em "pt" (nomes, termos técnicos), preencha "en"
com a tradução de cada linha se quiser legenda em inglês, e não mexa nos tempos.
"""
import argparse
import sys
import json
import os
import re

CURTAS = {"o", "a", "e", "de", "da", "do", "que", "com", "pra", "uma", "um", "na", "no", "em", "os", "as"}


def no_tempo_novo(edl):
    """Para cada bloco mantido: (ini, fim, deslocamento no vídeo cortado)."""
    mapa, t = [], 0.0
    for b in edl:
        if b.get("manter", True):
            mapa.append((b["ini"], b["fim"], t))
            t += b["fim"] - b["ini"]
    return mapa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--max", type=int, default=32)
    a = ap.parse_args()
    palavras = json.load(open(os.path.join(a.pasta, "palavras.json"), encoding="utf-8"))
    edl = json.load(open(os.path.join(a.pasta, "edl.json"), encoding="utf-8"))
    mapa = no_tempo_novo(edl)
    ws = []
    for p in palavras:
        for ini, fim, off in mapa:
            if ini - 0.01 <= p["s"] and p["e"] <= fim + 0.01:
                ws.append({"w": p["w"], "s": p["s"] - ini + off, "e": p["e"] - ini + off, "bloco": off})
                break
    # maiúscula depois de ponto final
    for i, w in enumerate(ws):
        anterior = ws[i - 1]["w"] if i else "."
        if re.search(r"[.?!]$", anterior) and w["w"]:
            w["w"] = w["w"][0].upper() + w["w"][1:]
    linhas, atual = [], []
    for i, w in enumerate(ws):
        atual.append(w)
        txt = " ".join(x["w"] for x in atual)
        prox = ws[i + 1] if i + 1 < len(ws) else None
        quebra = (prox is None
                  or re.search(r"[.?!]$", w["w"])                       # fim de frase sempre fecha a linha
                  or len(txt + " " + prox["w"]) > a.max
                  or (re.search(r"[,:]$", w["w"]) and len(txt) >= 14))
        if quebra:
            linhas.append(atual)
            atual = []
    # palavra curta de ligação não fecha linha
    for k in range(len(linhas) - 1):
        while len(linhas[k]) > 2 and linhas[k][-1]["w"].lower() in CURTAS:
            linhas[k + 1].insert(0, linhas[k].pop())
    # palavra solta no fim de frase volta pra linha de cima, se couber
    k = 1
    while k < len(linhas):
        txt = " ".join(x["w"] for x in linhas[k])
        if len(txt) < 15 and re.search(r"[.?!]$", txt) and len(" ".join(x["w"] for x in linhas[k - 1] + linhas[k])) <= a.max + 12 \
                and not re.search(r"[.?!]$", linhas[k - 1][-1]["w"]):
            linhas[k - 1] += linhas.pop(k)
        else:
            k += 1
    saida = []
    for k, l in enumerate(linhas):
        if not l:
            continue
        saida.append({"pt": " ".join(x["w"] for x in l), "en": "", "ini": round(l[0]["s"], 3), "fim": round(l[-1]["e"], 3)})
    for k, s in enumerate(saida):        # sem buraco curto entre linhas: a legenda não pisca
        if k + 1 < len(saida) and saida[k + 1]["ini"] - s["fim"] < 0.45:
            s["fim"] = saida[k + 1]["ini"]
        else:
            s["fim"] = round(s["fim"] + 0.2, 3)
    json.dump(saida, open(os.path.join(a.pasta, "legendas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(saida)} linhas em {a.pasta}/legendas.json\n")
    for s in saida:
        print(f"{s['ini']:6.2f}-{s['fim']:6.2f}  {s['pt']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
