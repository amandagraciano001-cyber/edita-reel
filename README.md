# Edita reel

Uma skill gratuita pro Claude Code que edita o seu reel falado sem você abrir nenhum editor.

Você grava falando pra câmera, chama `/edita-reel` e o Claude:

1. **Transcreve no seu computador**, sem mandar nada pra internet e sem custo.
2. **Propõe os cortes**: pausas, tomadas repetidas, frase que começou errado. Você aprova antes.
3. **Dá ritmo**: a câmera aproxima devagar na primeira frase e depois alterna plano aberto e fechado a cada frase, como se houvesse cortes.
4. **Coloca a arte**: capa grande com a frase mais forte, título pequeno no alto, legenda com a palavra que está sendo dita em destaque, print flutuando quando você cita um site ou produto, número grande, lista acendendo, e o fecho ("Comenta PALAVRA" ou o seu link).
5. **Exporta em 9:16**, pronto pra Instagram, TikTok e Shorts. Vídeo do iPhone em HDR continua HDR.
6. **Guarda no Estúdio**: uma página local com todos os vídeos prontos, a legenda de cada um pra copiar, a palavra-chave e o estado (pronto, programado, postado).

Depois é só dar recado, como pra uma editora: "corta a frase do meio", "abre pela frase mais forte", "troca a capa", "tira o print", "acelera 1.1".

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

Já tinha a versão anterior? Repita o `cp -r` por cima: os arquivos novos entram e os antigos continuam funcionando do mesmo jeito.

## Como usar

Abra o Claude Code e peça:

```
/edita-reel o vídeo está em ~/Downloads/meu-video.MOV. Eu cito o site da ferramenta, o print está em ~/Downloads/print.png. É pro Instagram, palavra-chave GUIA.
```

Na primeira vez, ele baixa o modelo de transcrição (alguns minutos, uma vez só).

## Dicas pra gravar

- Fale direto pra câmera e respire entre as frases: a pausa vira ponto de corte, e cada frase vira um "corte" de plano.
- Errou? Repita a frase inteira. O Claude percebe a tomada repetida e propõe ficar com a melhor.
- Diga a frase mais forte do vídeo em até 6 palavras em algum momento: ela vira a capa.
- Cite as coisas pelo nome (o site, a ferramenta, o número): cada uma vira uma arte na tela.
- Grave na vertical, com o rosto no terço de cima. Se gravar na horizontal, ele recorta o centro.
- Vídeo do iPhone em HDR é tratado: a cor não lava e a legenda não fica apagada.

## O que vem em cada arquivo

| Arquivo | O que faz |
|---|---|
| `edita-reel/SKILL.md` | O passo a passo que o Claude segue |
| `scripts/transcrever.py` | Transcrição local com o tempo de cada palavra |
| `scripts/cortes.py` | Separa a fala em frases e tira as pausas |
| `scripts/legendas.py` | Legenda em duas linhas (português e inglês) no tempo do vídeo cortado, pra versão básica |
| `scripts/montar.py` | Corta, enquadra, acelera, clareia e exporta (com ou sem legenda) |
| `scripts/ritmo.py` | Zoom de abertura e alternância de plano a cada frase |
| `scripts/estilo.py` | As peças visuais: capa, título, legenda ativa, print flutuando, número, lista, fecho |
| `scripts/arte.py` | Lê um `arte.json` e põe tudo isso por cima do vídeo, numa camada só |
| `scripts/estudio.py` | A página local com os vídeos prontos, legendas e estado |
| `scripts/comum.py` | Tempo das palavras no vídeo cortado e o codificador certo (HDR ou SDR) |

## Novidades

**Outubro de 2026.** Ritmo (zoom de abertura e cortes de plano por frase), arte por cima do vídeo a partir de um JSON (capa, título, legenda com palavra ativa, prints com crédito, listas, números, fecho), opção de luz pra vídeo SDR escuro, abertura fria reordenando os blocos, e o Estúdio. A versão básica (corte + legenda em duas linhas) continua igual.

## Licença

MIT. Use, adapte e compartilhe.
