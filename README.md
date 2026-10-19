# Edita reel

Uma skill gratuita pro Claude Code e pro Codex que edita o seu reel falado sem você abrir nenhum editor.

Você grava falando pra câmera, chama `/edita-reel` (ou `$edita-reel` no Codex) e o agente:

1. **Transcreve no seu computador**, sem mandar nada pra internet e sem custo.
2. **Propõe os cortes**: pausas, tomadas repetidas, frase que começou errado. Você aprova antes.
3. **Dá ritmo**: a câmera aproxima devagar na primeira frase e depois alterna plano aberto e fechado a cada frase, como se houvesse cortes.
4. **Coloca a arte**: capa grande com a frase mais forte, título pequeno no alto, legenda com a palavra que está sendo dita em destaque, print flutuando quando você cita um site ou produto, número grande, lista acendendo, e o fecho ("Comenta PALAVRA" ou o seu link).
5. **Exporta em 9:16**, pronto pra Instagram, TikTok e Shorts. Vídeo do iPhone em HDR continua HDR.

Depois é só dar recado, como pra uma editora: "corta a frase do meio", "abre pela frase mais forte", "troca a capa", "tira o print", "acelera 1.1".

Feita por [Amanda Graciano](https://amandagraciano.com), a partir do processo que ela usa pra editar os próprios reels.

## Funciona em

Claude Code e Codex, no Mac, no Windows e no Linux. O instalador acha sozinho qual agente você tem e coloca a skill no lugar certo de cada um.

| Agente | Onde a skill fica | Como chamar |
|---|---|---|
| Claude Code | `~/.claude/skills/edita-reel` | `/edita-reel` |
| Codex | `~/.agents/skills/edita-reel` | `$edita-reel` |

## O que você precisa

- [Claude Code](https://claude.com/claude-code) ou [Codex](https://developers.openai.com/codex)

| | Mac | Windows | Linux |
|---|---|---|---|
| Python 3.9 ou mais novo | já vem no Mac (ou `brew install python`) | `winget install Python.Python.3.12` | `sudo apt install python3 python3-venv` |
| ffmpeg | `brew install ffmpeg` | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` |

O instalador cria uma pasta `.venv` dentro da skill com as bibliotecas (Pillow, numpy e a transcrição certa pro seu computador). A transcrição se ajusta sozinha:

| Computador | Como transcreve |
|---|---|
| Mac com chip Apple | mlx-whisper, no próprio chip. Rápido. |
| Windows ou Linux com placa NVIDIA | faster-whisper na placa, se as bibliotecas CUDA 12 estiverem instaladas; sem elas, cai sozinho pro processador. |
| Sem placa de vídeo (e Mac Intel) | faster-whisper no processador. Mais lento: um reel de 1 minuto pode levar alguns minutos. Se ficar lento demais, use o modelo menor com a variável `EDITA_REEL_MODELO=small`. |

Vídeo HDR do iPhone continua HDR. Vídeo HDR10 (o de alguns Android) sai em cor normal, com aviso.

## Como instalar

**Jeito mais fácil:** abra o Claude Code ou o Codex e cole:

```
https://github.com/amandagraciano001-cyber/edita-reel

Instala essa skill pra mim e confere se as dependências estão instaladas.
```

**Pelo instalador.** Baixe o repositório (com o `git clone` abaixo, ou pelo botão Code > Download ZIP aqui no GitHub) e rode o instalador dentro da pasta.

Mac ou Linux, no Terminal:

```bash
git clone https://github.com/amandagraciano001-cyber/edita-reel.git
cd edita-reel
bash instalar.sh
```

Windows, no PowerShell:

```powershell
git clone https://github.com/amandagraciano001-cyber/edita-reel.git
cd edita-reel
powershell -ExecutionPolicy Bypass -File instalar.ps1
```

Pra instalar só num agente: `--claude` ou `--codex` no Mac e no Linux, `-Claude` ou `-Codex` no Windows. Já tinha instalado? Rode o instalador de novo: ele troca os arquivos e mantém o que já foi baixado.

## Como usar

No Claude Code a skill é chamada com `/edita-reel`; no Codex, com `$edita-reel`. O resto do pedido é igual.

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
| `instalar.sh` e `instalar.ps1` | Os instaladores do Mac e Linux e do Windows |
| `edita-reel/agents/openai.yaml` | O nome e a descrição que o Codex mostra |
| `edita-reel/SKILL.md` | O passo a passo que o agente segue |
| `scripts/transcrever.py` | Transcrição local com o tempo de cada palavra |
| `scripts/cortes.py` | Separa a fala em frases e tira as pausas |
| `scripts/legendas.py` | Legenda em duas linhas (português e inglês) no tempo do vídeo cortado, pra versão básica |
| `scripts/montar.py` | Corta, enquadra, acelera, clareia e exporta (com ou sem legenda) |
| `scripts/ritmo.py` | Zoom de abertura e alternância de plano a cada frase |
| `scripts/estilo.py` | As peças visuais: capa, título, legenda ativa, print flutuando, número, lista, fecho |
| `scripts/arte.py` | Lê um `arte.json` e põe tudo isso por cima do vídeo, numa camada só |
| `scripts/comum.py` | Tempo das palavras no vídeo cortado e o codificador certo (HDR ou SDR) |

## A família

Edita reel é a do meio de três skills que funcionam juntas, cada uma sozinha também:

1. **[Roteiro reel](https://github.com/amandagraciano001-cyber/roteiro-reel)**: antes de gravar. Ideia entra, roteiro sai, com capa, legendas e palavra-chave. O roteiro vira o `arte.json` desta skill com um comando.
2. **Edita reel** (esta): depois de gravar. Vídeo bruto entra, reel editado sai.
3. **[Estúdio reel](https://github.com/amandagraciano001-cyber/estudio-reel)**: depois de editar. Os vídeos prontos viram fila, calendário e histórico.

## Novidades

**Outubro de 2026.** Ritmo (zoom de abertura e cortes de plano por frase), arte por cima do vídeo a partir de um JSON (capa, título, legenda com palavra ativa, prints com crédito, listas, números, fecho), opção de luz pra vídeo SDR escuro, abertura fria reordenando os blocos. O Estúdio, que nasceu aqui, virou a skill própria Estúdio reel. A versão básica (corte + legenda em duas linhas) continua igual.

## Licença

MIT. Use, adapte e compartilhe.
