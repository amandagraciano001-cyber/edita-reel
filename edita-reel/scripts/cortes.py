"""Propõe os cortes: separa a fala em blocos e tira as pausas entre eles.

Uso:
    python cortes.py PASTA [--pausa 0.35] [--folga 0.12]

Lê PASTA/palavras.json e grava PASTA/edl.json, uma lista de blocos:
    {"n": 1, "ini": 0.42, "fim": 3.91, "manter": true, "texto": "..."}

Um bloco termina no fim de cada frase (ponto, interrogação, exclamação) ou quando
o silêncio entre duas palavras passa de --pausa segundos. Assim dá pra tirar uma
frase inteira sem mexer nas outras. A --folga é o respiro antes e depois de cada
bloco; entre frases ditas sem pausa, o corte cai no meio do espaço entre elas.

Depois de rodar: leia a lista, marque "manter": false nos blocos que são erro,
tomada repetida ou fala que não entra, e só então monte o vídeo.
"""
import argparse
import sys
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--pausa", type=float, default=0.35)
    ap.add_argument("--folga", type=float, default=0.12)
    a = ap.parse_args()
    palavras = json.load(open(os.path.join(a.pasta, "palavras.json"), encoding="utf-8"))
    if not palavras:
        raise SystemExit("Nenhuma palavra na transcrição.")
    blocos, atual = [], [palavras[0]]
    for p in palavras[1:]:
        fim_de_frase = atual[-1]["w"].rstrip().endswith((".", "?", "!"))
        if p["s"] - atual[-1]["e"] > a.pausa or fim_de_frase:
            blocos.append(atual)
            atual = [p]
        else:
            atual.append(p)
    blocos.append(atual)
    edl = []
    for b in blocos:
        ini = max(0.0, b[0]["s"] - a.folga)
        fim = b[-1]["e"] + a.folga
        if edl and ini < edl[-1]["fim"]:          # folgas se encostaram: corta no meio do espaço
            meio = round((edl[-1]["_ultima"] + b[0]["s"]) / 2, 3)
            edl[-1]["fim"] = meio
            ini = meio
        edl.append({"n": len(edl) + 1, "ini": round(ini, 3), "fim": round(fim, 3),
                    "manter": True, "texto": " ".join(x["w"] for x in b), "_ultima": b[-1]["e"]})
    for b in edl:
        b.pop("_ultima", None)
    json.dump(edl, open(os.path.join(a.pasta, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(b["fim"] - b["ini"] for b in edl)
    print(f"{len(edl)} blocos, {total:.1f}s de fala (pausas removidas)\n")
    for b in edl:
        print(f"[{b['n']:2d}] {b['ini']:7.2f}-{b['fim']:7.2f}  {b['texto']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
