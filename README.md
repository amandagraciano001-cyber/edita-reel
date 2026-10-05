# Edita reel

Uma skill gratuita pro Claude Code que edita o seu reel falado sem você abrir nenhum editor.

Você grava falando pra câmera, chama `/edita-reel` e o Claude:

1. **Transcreve no seu computador**, sem mandar nada pra internet e sem custo.
2. **Propõe os cortes**: pausas, tomadas repetidas, frase que começou errado. Você aprova antes.
3. **Coloca a legenda** em português, e em inglês embaixo se você quiser.
4. **Acelera** se você pedir (1.1 é um bom ponto de partida).
5. **Exporta em 9:16**, pronto pra Instagram, TikTok e Shorts.

Depois é só dar recado, como pra uma editora: "corta a frase do meio", "acelera 1.1", "tira o áudio que eu ponho música no app".

Feita por [Amanda Graciano](https://amandagraciano.com), a partir do processo que ela usa pra editar os próprios reels.

## O que você precisa

- [Claude Code](https://claude.com/claude-code)
- Mac (de preferência com chip Apple) ou Linux
- [ffmpeg](https://ffmpeg.org): no Mac, `brew install ffmpeg`
- Python 3.10 ou mais novo

## Como instalar

**Jeito mais fácil:** abra o Claude Code e cole:

```
https://github.com/amandagraciano001-cyber/edita-reel

Instala essa skill pra mim e confere se as dependências estão instaladas.
```

**Ou você mesma:**

```bash
git clone https://github.com/amandagraciano001-cyber/edita-reel.git edita-reel
cp -r edita-reel/edita-reel ~/.claude/skills/
pip install -r ~/.claude/skills/edita-reel/requirements.txt
```

## Como usar

Abra o Claude Code e peça:

```
/edita-reel o vídeo está em ~/Downloads/meu-video.MOV, quero legenda em inglês e acelerar 1.1
```

Na primeira vez, ele baixa o modelo de transcrição (alguns minutos, uma vez só).

## Dicas pra gravar

- Fale direto pra câmera e respire entre as frases: a pausa vira ponto de corte.
- Errou? Repita a frase inteira. O Claude percebe a tomada repetida e propõe ficar com a melhor.
- Grave na vertical. Se gravar na horizontal, ele recorta o centro.
- Vídeo do iPhone em HDR é tratado: a cor não lava e a legenda não fica apagada.

## O que vem em cada arquivo

| Arquivo | O que faz |
|---|---|
| `edita-reel/SKILL.md` | O passo a passo que o Claude segue |
| `scripts/transcrever.py` | Transcrição local com o tempo de cada palavra |
| `scripts/cortes.py` | Separa a fala em frases e tira as pausas |
| `scripts/legendas.py` | Monta a legenda no tempo do vídeo cortado |
| `scripts/montar.py` | Corta, enquadra, legenda, acelera e exporta |

## Licença

MIT. Use, adapte e compartilhe.
