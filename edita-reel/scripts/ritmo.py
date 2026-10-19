"""Dá ritmo ao take único: zoom lento de abertura e "cortes" a cada bloco de fala, alternando plano aberto e fechado.

Uso:
    python ritmo.py VIDEO PASTA [--velocidade 1.0] [--sem-alternar] [--fechado 1.22] [--alto 0.34] [--saida ARQUIVO]

VIDEO é o reel já cortado por montar.py (de preferência sem legenda: a arte e a legenda entram depois, com arte.py).
PASTA é a pasta edita-reel/ do vídeo (palavras.json e edl.json), pra saber onde cada frase começa e termina.
--velocidade precisa ser a mesma usada no montar.py, senão as frases caem no lugar errado.

O que ele faz, do jeito que os reels falados que prendem fazem:
- nos primeiros segundos (até o fim da primeira frase) a câmera aproxima devagar, de 1,0 até 1,12;
- depois, a cada frase do edl (e a cada pausa maior que 0,35 s dentro dela), alterna plano aberto (1,0) e fechado (--fechado).
  Blocos menores que 1,4 s grudam no seguinte, pra não virar metralhadora.
- --alto diz onde fica o rosto na vertical (0 = topo, 1 = base) pra o zoom fechar nele, não no peito.
Vídeo HDR do iPhone continua HDR. Grava PASTA/reel-ritmo.mp4 (ou --saida).
"""
import argparse
import os
import subprocess

from comum import (W, H, blocos_do_reel, codificador, eh_hdr, fim_da_primeira_frase, palavras_no_reel)


def alterna(blocos, aberto=1.0, fechado=1.22, minimo=1.4, depois_de=0.0):
    grupos, atual = [], None
    for ini, fim in blocos:
        if atual and (atual[1] - atual[0]) < minimo:
            atual = (atual[0], fim)
        else:
            if atual:
                grupos.append(atual)
            atual = (ini, fim)
    if atual:
        grupos.append(atual)
    out, fechado_agora = [], False
    for k, (ini, fim) in enumerate(grupos):
        prox = grupos[k + 1][0] if k + 1 < len(grupos) else fim + 60   # o plano segura até o próximo corte, sem voltar a 1,0 na pausa
        ini = max(ini, depois_de)
        if prox - ini < minimo:                                        # sobra curta demais depois da abertura: não vira corte
            continue
        z = fechado if fechado_agora else aberto
        fechado_agora = not fechado_agora
        out.append((ini, prox, z, z))
    return out


def zoom_trechos(entrada, saida, trechos, alto=0.34):
    """trechos: (ini, fim, z_ini, z_fim). Entre ini e fim o zoom vai de z_ini a z_fim; fora deles fica 1,0."""
    expr = "1"
    for ini, fim, za, zb in reversed(sorted(trechos)):
        seg = (f"({za:.4f}+({zb - za:.4f})*(t-{ini:.3f})/{max(fim - ini, 0.01):.3f})"
               if abs(zb - za) > 1e-4 else f"{za:.4f}")
        expr = f"if(between(t,{ini:.3f},{fim:.3f}),{seg},{expr})"
    vf = (f"scale=w='trunc({W}*{expr}/2)*2':h='trunc({H}*{expr}/2)*2':eval=frame:flags=lanczos,"
          f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{alto}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", entrada, "-vf", vf, *codificador(eh_hdr(entrada)),
                    "-c:a", "copy", "-movflags", "+faststart", saida], check=True)
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("pasta")
    ap.add_argument("--velocidade", type=float, default=1.0)
    ap.add_argument("--sem-alternar", action="store_true", help="só o zoom de abertura, sem cortes depois")
    ap.add_argument("--fechado", type=float, default=1.22)
    ap.add_argument("--alto", type=float, default=0.34)
    ap.add_argument("--saida")
    a = ap.parse_args()
    palavras = palavras_no_reel(a.pasta, a.velocidade)
    if not palavras:
        raise SystemExit("Nenhuma palavra dentro dos blocos mantidos. A --velocidade é a mesma do montar.py?")
    f1 = fim_da_primeira_frase(palavras)
    trechos = [(0.0, f1, 1.0, 1.12)]
    if a.sem_alternar:
        trechos.append((f1, 1e5, 1.12, 1.12))
    else:
        trechos += alterna(blocos_do_reel(a.pasta, a.velocidade), aberto=1.0, fechado=a.fechado, depois_de=f1)
    saida = a.saida or os.path.join(a.pasta, "reel-ritmo.mp4")
    zoom_trechos(a.video, saida, trechos, a.alto)
    n = len(trechos) - 1
    print(f"Pronto: {saida}  (abertura até {f1:.1f}s, {n} {'trecho' if n == 1 else 'trechos'} de plano depois)")
    for ini, fim, za, zb in trechos[1:]:
        print(f"  {ini:6.2f}-{min(fim, 9999):6.2f}  {'fechado' if za > 1.05 else 'aberto'}")


if __name__ == "__main__":
    main()
