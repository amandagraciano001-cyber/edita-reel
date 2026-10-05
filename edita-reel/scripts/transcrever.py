"""Transcreve o áudio de um vídeo no seu computador, com o tempo de cada palavra.

Uso:
    python transcrever.py VIDEO [--idioma pt] [--saida PASTA]

Gera em PASTA (padrão: pasta do vídeo, subpasta edita-reel/):
    palavras.json   lista de {"w": palavra, "s": início, "e": fim} em segundos
    transcricao.txt texto por trecho, com o tempo de início

Usa o mlx-whisper (Mac com chip Apple). Se não estiver instalado, tenta o
faster-whisper. Nada sai do seu computador.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import wave

MODELO_MLX = "mlx-community/whisper-large-v3-turbo"


def extrair_audio(video, destino):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1",
                    "-ar", "16000", destino], check=True)


def com_mlx(wav, idioma):
    import mlx_whisper
    import numpy as np
    w = wave.open(wav)
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    r = mlx_whisper.transcribe(a, path_or_hf_repo=MODELO_MLX, language=idioma,
                               word_timestamps=True, verbose=None)
    palavras = [{"w": x["word"].strip(), "s": round(x["start"], 3), "e": round(x["end"], 3)}
                for s in r["segments"] for x in s.get("words", [])]
    trechos = [(s["start"], s["text"].strip()) for s in r["segments"]]
    return palavras, trechos


def com_faster(wav, idioma):
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3", compute_type="int8")
    segs, _ = m.transcribe(wav, language=idioma, word_timestamps=True)
    palavras, trechos = [], []
    for s in segs:
        trechos.append((s.start, s.text.strip()))
        for x in s.words or []:
            palavras.append({"w": x.word.strip(), "s": round(x.start, 3), "e": round(x.end, 3)})
    return palavras, trechos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--saida")
    a = ap.parse_args()
    saida = a.saida or os.path.join(os.path.dirname(os.path.abspath(a.video)), "edita-reel")
    os.makedirs(saida, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        extrair_audio(a.video, wav)
        try:
            palavras, trechos = com_mlx(wav, a.idioma)
        except ImportError:
            try:
                palavras, trechos = com_faster(wav, a.idioma)
            except ImportError:
                sys.exit("Instale a transcrição local: pip install mlx-whisper (Mac com chip Apple) "
                         "ou pip install faster-whisper")
    palavras = [p for p in palavras if p["w"]]
    json.dump(palavras, open(os.path.join(saida, "palavras.json"), "w"), ensure_ascii=False, indent=0)
    with open(os.path.join(saida, "transcricao.txt"), "w") as f:
        for ini, txt in trechos:
            f.write(f"{ini:7.2f}  {txt}\n")
    print(f"{len(palavras)} palavras em {saida}/palavras.json")
    print(open(os.path.join(saida, "transcricao.txt")).read())


if __name__ == "__main__":
    main()
