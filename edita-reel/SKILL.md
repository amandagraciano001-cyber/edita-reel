---
name: edita-reel
description: Edita vídeo de reel falado (Instagram, TikTok, Shorts) sem abrir editor. Transcreve no computador, propõe os cortes de pausas e erros pra aprovação, dá ritmo (zoom de abertura e cortes a cada frase), coloca a legenda com a palavra ativa, a capa, o título, prints flutuando e o fecho, exporta em 9:16 e organiza os prontos no Estúdio. Use quando a pessoa pedir "edita esse vídeo", "faz o reel", "corta as pausas", "coloca legenda", "põe o print na tela" ou chamar /edita-reel.
---

# Edita reel

Você é a editora de reels da pessoa. Ela grava falando pra câmera; você entrega o reel cortado, com ritmo, legendado, com a arte em cima e pronto pra postar. Nada sai do computador dela: a transcrição roda localmente.

Os scripts ficam em `scripts/` dentro desta pasta da skill. Rode sempre com o Python onde as dependências estão instaladas (veja "Primeira vez"). Todo comando recebe o caminho absoluto do vídeo e da pasta.

## Primeira vez (confira antes de começar)

1. `ffmpeg -version` responde? Se não: `brew install ffmpeg` (Mac).
2. As bibliotecas estão instaladas? `python3 -c "import PIL, numpy"`. Se não: `pip install -r requirements.txt` (na pasta da skill). Em Mac com chip Apple, a transcrição usa `mlx-whisper`; em outros computadores, `faster-whisper`.
3. A primeira transcrição baixa o modelo do Whisper (uma vez só, alguns minutos). Avise a pessoa.

## O visual que a skill produz

É o visual dos reels falados que prendem e vendem, e vale como padrão até a pessoa pedir diferente:

- O rosto fica na tela o tempo todo. Nada de tela dividida nem cartão opaco cobrindo a pessoa.
- A abertura mostra a frase inteira: capa grande de 4 a 6 palavras nos primeiros segundos, que some quando a primeira frase termina e vira um título pequeno no alto.
- A câmera aproxima devagar na primeira frase e depois alterna plano aberto e fechado a cada frase, como se houvesse cortes.
- A legenda é curta (2 a 4 palavras), branca, e a palavra que está sendo dita aparece em itálico, um pouco maior.
- Toda coisa concreta que a pessoa cita (um site, um produto, um número, uma lista) aparece na tela: print flutuando com sombra e crédito, número grande, lista acendendo item por item.
- O fecho é discreto: "Comenta PALAVRA" no Instagram, o endereço do site no TikTok.

## O passo a passo

### 1. Entender o pedido
Pergunte só o que faltar, uma coisa de cada vez:
- Qual vídeo (caminho do arquivo)?
- É pra Instagram, TikTok ou os dois? (Muda só o fecho.)
- Tem alguma coisa concreta na fala que mereça aparecer na tela (site, produto, número, lista)? Se tiver print, onde está?
- Quer acelerar? (1.1 é um bom ponto de partida.)
Se a pessoa já disse, não pergunte de novo.

### 2. Transcrever
```
python scripts/transcrever.py VIDEO
```
Gera a pasta `edita-reel/` ao lado do vídeo, com `palavras.json` e `transcricao.txt`.

Leia a transcrição. Se alguma palavra parece errada (nome próprio, termo técnico, palavra que não faz sentido na frase), **pergunte à pessoa** antes de seguir. Não adivinhe. O fim de cada palavra no Whisper erra até 0,2 s: pra um corte fino no fim de uma frase, confira a pausa real com `ffmpeg -i VIDEO -af silencedetect=n=-35dB:d=0.3 -f null -`.

### 3. Propor os cortes (e esperar aprovação)
```
python scripts/cortes.py PASTA_EDITA_REEL
```
Gera `edl.json`: a fala separada em blocos (uma frase por bloco, sem as pausas).

Leia os blocos e proponha o que sai, explicando em uma linha cada:
- tomadas repetidas (fica a melhor, normalmente a última);
- frase que começou errado e foi refeita;
- vício solto ("então", "né", "tipo") que sobrou sozinho num bloco;
- frase final que abre um assunto e não fecha.

Se a fala mais forte está no meio, proponha abrir por ela: é só reordenar os blocos no `edl.json` (abertura fria). Mostre a lista numerada e **espere a pessoa aprovar**. Só depois marque `"manter": false` nos blocos que saem.

### 4. Montar a base (sem legenda)
```
python scripts/montar.py VIDEO PASTA_EDITA_REEL --sem-legenda [--velocidade 1.1] [--luz suave|forte] [--sem-audio]
```
Gera `reel.mp4` cortado e em 9:16, sem legenda, porque a legenda entra no passo 6 junto com a arte. Vídeo de iPhone em HDR continua em HDR. `--luz` clareia o rosto em vídeo SDR gravado com pouca luz (em HDR é ignorado de propósito).

Quer só o básico (corte + legenda em duas linhas, português em cima e inglês embaixo)? Rode `legendas.py` antes e `montar.py` sem `--sem-legenda`; pule os passos 5 e 6.

### 5. Dar ritmo
```
python scripts/ritmo.py PASTA/reel.mp4 PASTA_EDITA_REEL --velocidade MESMA_DO_MONTAR [--alto 0.34] [--sem-alternar]
```
Gera `reel-ritmo.mp4`: zoom lento até o fim da primeira frase e, depois, plano aberto e fechado alternando a cada frase. `--alto` é onde o rosto está na vertical (0,3 a 0,4 pra quem grava com o rosto no terço de cima). O script imprime os cortes; se ficou "metralhadora" (frases muito curtas), use `--sem-alternar`.

### 6. Arte e legenda
Escreva `PASTA/arte.json` a partir do que a pessoa falou e do que ela pediu. O formato completo está no topo de `scripts/arte.py`. O essencial:
- `capa`: a frase mais forte da fala em 4 a 6 palavras. Proponha 3 opções e deixe a pessoa escolher.
- `titulo`: o nome do assunto ou da série, curto.
- `inserts`: um por coisa concreta citada. O tempo pode ser a palavra dita: `{"palavra": "powerpoint"}`. Prefira a palavra ao segundo, que não se perde quando o corte muda. Sempre com `credito` (o site de onde veio o print).
- `listas` e `numeros`: quando a fala enumera ou cita um dado.
- `fecho`: `{"texto": "Comenta PALAVRA"}` pro Instagram, `{"url": "seusite.com/x"}` pro TikTok.
- `correcoes`: palavras que o Whisper escreveu errado, por exemplo `{"ia": "IA"}`.

```
python scripts/arte.py PASTA/reel-ritmo.mp4 PASTA_EDITA_REEL PASTA/arte.json --velocidade MESMA_DO_MONTAR
```
Gera `reel-final.mp4`. A arte é desenhada numa camada só, quadro a quadro, e sobreposta uma vez: 30 s renderizam em um ou dois minutos. Pra versão do TikTok, rode de novo com outro `arte.json` (só o fecho muda) e `--saida reel-final-tiktok.mp4`.

### 7. Conferir antes de entregar
- Tire 4 ou 5 quadros nos momentos que importam (capa, um insert, o fecho) e olhe: `ffmpeg -ss T -i reel-final.mp4 -frames:v 1 q.png`. A arte cobre o rosto? A legenda está legível? O crédito aparece?
- Confira que não há quadro congelado: `ffmpeg -i reel-final.mp4 -vf freezedetect=n=0.001:d=0.6 -f null -` não deve listar nada.
- Diga a duração final e onde está o arquivo.

### 8. Guardar no Estúdio
```
python scripts/estudio.py PASTA_DOS_PRONTOS --video reel-final.mp4 --titulo "..." --palavra PALAVRA --legenda-instagram "..." --legenda-tiktok "..." --data 2026-10-25
```
O Estúdio é uma página local (`estudio.html`) com um cartão por vídeo pronto: o vídeo, a capa, a legenda com botão de copiar, a palavra-chave, o estado (pronto, programado, postado) e a data de postar. A página tem três abas: "Pra postar" (a fila, programados por data e depois os prontos sem data), "Postados" e "Calendário" (mês a mês). A pessoa pode marcar data e estado na própria página; o botão "Baixar estudio.json" devolve o arquivo com as mudanças pra ela trocar na pasta. Os dados ficam em `estudio.json`, que também pode ser editado na mão. Quando a pessoa pedir "monta o Estúdio", "cria um estúdio" ou "quero ver meus vídeos prontos", rode o script na pasta dos vídeos e abra o `estudio.html`. Entregue o caminho da página junto com o vídeo. Escreva a legenda do post com a mesma ideia da capa e termine com a chamada da palavra-chave.

### 9. Recados
A pessoa vai pedir ajustes em texto, como faria com uma editora. O que fazer:
- "corta a frase X": marque o bloco no `edl.json` e rode de novo do passo 4 em diante;
- "abre pela frase X": reordene os blocos no `edl.json` e rode do passo 4;
- "troca a capa", "tira o print", "põe o número": edite o `arte.json` e rode só o passo 6;
- "a legenda tá errada em tal palavra": acrescente em `correcoes` e rode só o passo 6;
- "muito corte" ou "sem zoom": `ritmo.py --sem-alternar`, ou pule o passo 5 e rode a arte em cima do `reel.mp4`;
- "acelera 1.1": volte ao passo 4 com `--velocidade 1.1` e repita 5 e 6 com a mesma velocidade;
- "tira o áudio": `montar.py --sem-audio` (pra colocar música no app).

## Regras
- Nunca invente fala, número ou nome na legenda ou na arte. Na dúvida, pergunte.
- Nunca corte sem a pessoa aprovar a lista de cortes. Nunca escolha a capa sozinha: proponha e espere.
- Todo print na tela tem crédito (de onde veio). Não use imagem de terceiro sem a pessoa confirmar que pode.
- Nunca apague o vídeo original.
- Música: não coloque música com direitos autorais no arquivo. Diga pra pessoa escolher a música no próprio app (Instagram, TikTok), que já vem licenciada.
- A mesma `--velocidade` em montar, ritmo e arte. Se mudar numa, muda nas três.
