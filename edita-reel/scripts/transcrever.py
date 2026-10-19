"""Transcreve o áudio de um vídeo no seu computador, com o tempo de cada palavra.

Uso:
    python transcrever.py VIDEO [--idioma pt] [--saida PASTA]

Gera em PASTA (padrão: pasta do vídeo, subpasta edita-reel/):
    palavras.json   lista de {"w": palavra, "s": início, "e": fim} em segundos
    transcricao.txt texto por trecho, com o tempo de início

Mac com chip Apple: usa o mlx-whisper. Windows, Linux e Mac Intel: usa o faster-whisper, na placa de
vídeo NVIDIA se houver. Nada sai do seu computador; o modelo é baixado uma vez só.
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


def ler_wav(wav):
    """O áudio já decodificado pelo ffmpeg (16 kHz, mono) como números. Entregar assim evita a leitura de arquivo
    das bibliotecas de transcrição, que muda de versão pra versão."""
    import numpy as np
    w = wave.open(wav)
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


def com_mlx(wav, idioma):
    import mlx_whisper
    a = ler_wav(wav)
    r = mlx_whisper.transcribe(a, path_or_hf_repo=MODELO_MLX, language=idioma,
                               word_timestamps=True, verbose=None)
    palavras = [{"w": x["word"].strip(), "s": round(x["start"], 3), "e": round(x["end"], 3)}
                for s in r["segments"] for x in s.get("words", [])]
    trechos = [(s["start"], s["text"].strip()) for s in r["segments"]]
    return palavras, trechos


def com_faster(wav, idioma):
    """Windows, Linux e Mac Intel. Usa a placa de vídeo NVIDIA quando existe (bem mais rápido); senão, o processador.
    EDITA_REEL_MODELO troca o modelo (ex.: small, medium) se o computador for lento."""
    import ctranslate2
    from faster_whisper import WhisperModel
    gpu = ctranslate2.get_cuda_device_count() > 0
    modelo = os.environ.get("EDITA_REEL_MODELO", "large-v3-turbo")
    print(f"Transcrevendo com {modelo} na {'placa de vídeo' if gpu else 'CPU (pode levar alguns minutos)'}...", flush=True)
    try:
        m = WhisperModel(modelo, device="cuda" if gpu else "cpu", compute_type="float16" if gpu else "int8")
        segs, _ = m.transcribe(ler_wav(wav), language=idioma, word_timestamps=True)
        segs = list(segs)
    except Exception as erro:          # placa NVIDIA sem as bibliotecas CUDA: volta pro processador
        if not gpu:
            raise
        print(f"A placa de vídeo não respondeu ({erro.__class__.__name__}); seguindo no processador.", flush=True)
        m = WhisperModel(modelo, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(ler_wav(wav), language=idioma, word_timestamps=True)
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
    json.dump(palavras, open(os.path.join(saida, "palavras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    with open(os.path.join(saida, "transcricao.txt"), "w", encoding="utf-8") as f:
        for ini, txt in trechos:
            f.write(f"{ini:7.2f}  {txt}\n")
    print(f"{len(palavras)} palavras em {saida}/palavras.json")
    print(open(os.path.join(saida, "transcricao.txt"), encoding="utf-8").read())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
