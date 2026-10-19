#!/usr/bin/env bash
# Instala a skill Edita reel no Claude Code e/ou no Codex, no Mac ou no Linux.
# Uso: bash instalar.sh            (acha sozinho os agentes instalados)
#      bash instalar.sh --claude   (só Claude Code)   |   bash instalar.sh --codex   (só Codex)
set -euo pipefail
NOME="edita-reel"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SISTEMA="$(uname -s)"
alvos=()
for a in "$@"; do
  case "$a" in
    --claude) alvos+=("$HOME/.claude/skills") ;;
    --codex)  alvos+=("$HOME/.agents/skills") ;;
    *) echo "Uso: bash instalar.sh [--claude] [--codex]"; exit 2 ;;
  esac
done
if [ ${#alvos[@]} -eq 0 ]; then
  if [ -d "$HOME/.claude" ] || command -v claude >/dev/null 2>&1; then alvos+=("$HOME/.claude/skills"); fi
  if [ -d "$HOME/.codex" ] || [ -d "$HOME/.agents" ] || command -v codex >/dev/null 2>&1; then alvos+=("$HOME/.agents/skills"); fi
fi
if [ ${#alvos[@]} -eq 0 ]; then
  echo "Não encontrei o Claude Code nem o Codex neste computador. Rode de novo com --claude ou --codex."; exit 1
fi

dica() {
  if [ "$SISTEMA" = "Darwin" ]; then echo "  No Mac: brew install $1   (sem o Homebrew? https://brew.sh)";
  elif command -v apt-get >/dev/null 2>&1; then echo "  No Ubuntu/Debian: sudo apt install $2";
  elif command -v dnf >/dev/null 2>&1; then echo "  No Fedora: sudo dnf install $2";
  else echo "  Instale $1 pelo gerenciador de pacotes do seu sistema."; fi
}
falta=0
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; assert sys.version_info >= (3,9)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "Falta o Python 3.9 ou mais novo."; dica python python3; falta=1
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Falta o ffmpeg."; dica ffmpeg ffmpeg; falta=1
fi
[ "$falta" -eq 0 ] || { echo "Instale o que falta e rode o instalador de novo."; exit 1; }

for base in "${alvos[@]}"; do
  destino="$base/$NOME"
  mkdir -p "$destino"
  find "$destino" -mindepth 1 -maxdepth 1 ! -name .venv -exec rm -rf {} +
  cp -R "$AQUI/$NOME/." "$destino/"
  echo "Copiado para $destino"
  if [ ! -x "$destino/.venv/bin/python" ]; then "$PY" -m venv "$destino/.venv"; fi
  echo "Instalando as bibliotecas (uma vez só, pode levar alguns minutos)..."
  "$destino/.venv/bin/python" -m pip install -q --upgrade pip
  "$destino/.venv/bin/python" -m pip install -q -r "$destino/requirements.txt"
  if [ "$SISTEMA" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    echo "  Mac com chip Apple: a transcrição usa o mlx-whisper, no chip."
  elif command -v nvidia-smi >/dev/null 2>&1; then
    echo "  Placa NVIDIA encontrada: a transcrição tenta usar a placa (precisa das bibliotecas CUDA 12; sem elas, roda no processador)."
  else
    echo "  A transcrição vai rodar no processador. Se ficar lenta, use EDITA_REEL_MODELO=small."
  fi
done

echo ""
echo "Pronto. Abra uma sessão nova do agente e chame:"
for base in "${alvos[@]}"; do
  case "$base" in
    */.claude/skills) echo "  Claude Code: /$NOME" ;;
    */.agents/skills) echo "  Codex: \$$NOME" ;;
  esac
done
