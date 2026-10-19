"""As peças visuais do reel falado: capa grande, título no alto, legenda com a palavra ativa, print flutuando,
número grande, lista acendendo e o fecho. Tudo desenhado em PIL, em camadas transparentes de 1080x1920.

O visual segue o que funciona nos reels falados que vendem: o rosto fica na tela o tempo todo, a legenda é
curta e branca com a palavra falada em itálico, o título é pequeno e espaçado no alto, e os prints flutuam
sobre o vídeo com sombra, sem cartão opaco e sem tela dividida. Só a capa dos primeiros segundos é grande.

Fontes: usa as que encontrar no computador. Mac: Helvetica Neue condensada (e Montserrat e Fraunces, se
estiverem instaladas). Windows: Bahnschrift, Segoe UI e Georgia. Linux: Liberation e DejaVu. Troque os caminhos em FONTES se quiser.
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
BRANCO = (255, 255, 255)

def _win(nome):
    return os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", nome)


FONTES = {
    # (caminho, índice dentro do .ttc, nome da variação)  -- o primeiro que existir vence
    "condensada": [("/System/Library/Fonts/HelveticaNeue.ttc", 9, None),
                   ("/Library/Fonts/Arial Bold.ttf", 0, None),
                   ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0, None),
                   (_win("bahnschrift.ttf"), 0, "Bold Condensed"),
                   (_win("arialbd.ttf"), 0, None),
                   ("/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf", 0, None),
                   ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0, None)],
    "normal": [("/System/Library/Fonts/HelveticaNeue.ttc", 0, None),
               ("/System/Library/Fonts/Supplemental/Arial.ttf", 0, None),
               (_win("segoeui.ttf"), 0, None),
               (_win("arial.ttf"), 0, None),
               ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 0, None),
               ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0, None)],
    "rotulo": [(os.path.expanduser("~/Library/Fonts/Montserrat.ttf"), 0, "SemiBold"),
               ("/System/Library/Fonts/HelveticaNeue.ttc", 1, None),
               ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0, None),
               (_win("seguisb.ttf"), 0, None),
               (_win("arialbd.ttf"), 0, None),
               ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0, None)],
    "italico": [(os.path.expanduser("~/Library/Fonts/Fraunces-Italic-VariableFont_SOFT,WONK,opsz,wght.ttf"), 0, "axes"),
                ("/System/Library/Fonts/Supplemental/Georgia Italic.ttf", 0, None),
                ("/System/Library/Fonts/Supplemental/Arial Italic.ttf", 0, None),
                (_win("georgiai.ttf"), 0, None),
                (_win("ariali.ttf"), 0, None),
                ("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", 0, None),
                ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", 0, None)],
}


def fonte(papel, tam):
    for caminho, idx, var in FONTES[papel]:
        if os.path.exists(caminho):
            try:
                f = ImageFont.truetype(caminho, tam, index=idx)
            except Exception:
                continue
            try:
                if var == "axes":
                    f.set_variation_by_axes([72, 500, 0, 0])
                elif var:
                    f.set_variation_by_name(var)
            except Exception:
                pass
            return f
    return ImageFont.load_default()


def base():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _sombra_texto(b, pos, txt, f, fill=BRANCO, raio=6, alpha=170, dx=0, dy=3):
    sh = base()
    ImageDraw.Draw(sh).text((pos[0] + dx, pos[1] + dy), txt, font=f, fill=(0, 0, 0, alpha))
    b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(raio)))
    ImageDraw.Draw(b).text(pos, txt, font=f, fill=fill + (255,))


def _quebra(d, txt, f, larg):
    ls, at = [], ""
    for w in txt.split():
        c = (at + " " + w).strip()
        if d.textlength(c, font=f) <= larg:
            at = c
        else:
            ls.append(at)
            at = w
    return [l for l in ls + [at] if l]


def capa_grande(txt, y0=150, tam=140, larg=W - 160):
    """Capa dos primeiros segundos: 4 a 6 palavras em caixa-alta condensada, branca, sombra suave, sem faixa."""
    b = base()
    d = ImageDraw.Draw(b)
    t = txt.upper()
    while True:
        f = fonte("condensada", tam)
        ls = _quebra(d, t, f, larg)
        if (len(ls) <= 2 and all(d.textlength(l, font=f) <= larg for l in ls)) or tam <= 90:
            break
        tam -= 6
    lh = int(tam * 0.96)
    for k, l in enumerate(ls):
        _sombra_texto(b, ((W - d.textlength(l, font=f)) / 2, y0 + k * lh), l, f, raio=10, alpha=190, dy=6)
    return b


def titulo_topo(txt, y=130, tam=30):
    """Título fixo: caixa-alta pequena, letras espaçadas, branca com sombra."""
    b = base()
    d = ImageDraw.Draw(b)
    f = fonte("rotulo", tam)
    t = txt.upper()
    esp = 4
    linhas, atual = [], ""
    for w in t.split():
        c = (atual + " " + w).strip()
        if sum(d.textlength(ch, font=f) + esp for ch in c) <= W - 160:
            atual = c
        else:
            linhas.append(atual)
            atual = w
    linhas.append(atual)
    for k, l in enumerate(linhas):
        larg = sum(d.textlength(ch, font=f) + esp for ch in l) - esp
        x = (W - larg) / 2
        yy = y + k * (tam + 14)
        for ch in l:
            _sombra_texto(b, (x, yy), ch, f, raio=4, alpha=160, dy=2)
            x += d.textlength(ch, font=f) + esp
    return b


def legenda_ativa(palavras, ativa, y=1400, tam=50):
    """Frase curta (2 a 4 palavras) branca e centralizada; a palavra que está sendo dita em itálico serifado, um pouco maior."""
    b = base()
    d = ImageDraw.Draw(b)
    f = fonte("normal", tam)
    fi = fonte("italico", int(tam * 1.18))
    esp = d.textlength(" ", font=f)
    partes = [(w, fi if i == ativa else f) for i, w in enumerate(palavras)]
    larg = sum(d.textlength(w, font=ff) for w, ff in partes) + esp * (len(partes) - 1)
    x = (W - larg) / 2
    for w, ff in partes:
        dy = -4 if ff is fi else 0
        _sombra_texto(b, (x, y + dy), w, ff, raio=5, alpha=200, dy=3)
        x += d.textlength(w, font=ff) + esp
    return b


def flutuante(img, x, y, larg, raio=28, sombra=True, rotulo=None, girar=0):
    """Print ou recorte flutuando sobre o vídeo: canto arredondado, sombra, sem fundo. (x, y) é o canto superior esquerdo."""
    b = base()
    im = img.convert("RGB") if img.mode != "RGB" else img
    esc = larg / im.width
    im = im.resize((max(int(im.width * esc), 1), max(int(im.height * esc), 1)), Image.LANCZOS)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], raio, fill=255)
    card = Image.new("RGBA", im.size, (0, 0, 0, 0))
    card.paste(im, (0, 0), m)
    if girar:
        card = card.rotate(girar, expand=True, resample=Image.BICUBIC)
    if sombra:
        sh = Image.new("RGBA", (card.width + 80, card.height + 80), (0, 0, 0, 0))
        sh.paste(Image.new("RGBA", card.size, (0, 0, 0, 150)), (40, 52), card.getchannel("A"))
        b.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)), (int(x) - 40, int(y) - 40))
    b.alpha_composite(card, (int(x), int(y)))
    if rotulo:
        _sombra_texto(b, (int(x), int(y) + card.height + 14), rotulo, fonte("rotulo", 24), raio=4, alpha=170, dy=2)
    return b


def numero_flutuante(num, rotulo, x=90, y=330, tam=260):
    """Número grande branco condensado com rótulo pequeno embaixo, flutuando no alto."""
    b = base()
    _sombra_texto(b, (x, y), str(num), fonte("condensada", tam), raio=10, alpha=190, dy=6)
    _sombra_texto(b, (x + 6, y + int(tam * 0.98)), rotulo.upper(), fonte("rotulo", 30), raio=4, alpha=170, dy=2)
    return b


def lista_topo(itens, ativos, x=90, y=330, tam=54, passo=84):
    """Lista acendendo: itens em caixa-alta condensada; os que ainda não foram ditos ficam apagados."""
    b = base()
    f = fonte("condensada", tam)
    fr = fonte("rotulo", 26)
    for i, item in enumerate(itens):
        titulo, sub = (item if isinstance(item, (list, tuple)) else (item, None))
        on = i < ativos
        im = base()
        _sombra_texto(im, (x, y + i * passo), str(titulo).upper(), f, raio=6, alpha=170 if on else 0, dy=3)
        if sub and on:
            ImageDraw.Draw(im).text((x + 4, y + i * passo + tam + 2), str(sub), font=fr, fill=(235, 235, 235, 255))
        if not on:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * 70 / 255)))
        b.alpha_composite(im)
    return b


def selo_url(rotulo, url, y=1260):
    """Fecho com endereço (pra TikTok, onde não tem palavra pra comentar): rótulo pequeno e o endereço grande."""
    b = base()
    d = ImageDraw.Draw(b)
    b.alpha_composite(titulo_topo(rotulo, y=y, tam=26))
    f = fonte("condensada", 62)
    _sombra_texto(b, ((W - d.textlength(url, font=f)) / 2, y + 44), url, f, raio=8, alpha=190, dy=4)
    return b
