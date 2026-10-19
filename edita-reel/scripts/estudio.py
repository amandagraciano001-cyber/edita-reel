"""O Estúdio: uma página local com os reels prontos, a legenda de cada um, a palavra-chave e o estado.

Uso:
    python estudio.py PASTA                                  varre os .mp4 da pasta e gera PASTA/estudio.html
    python estudio.py PASTA --video reel.mp4 --titulo "..." --legenda-instagram "..." --legenda-tiktok "..."
                            --palavra PALAVRA --estado pronto|programado|postado --nota "..."

Os dados ficam em PASTA/estudio.json (um item por vídeo), que você também pode editar na mão. A capa de cada
vídeo é tirada do segundo 1 e guardada em PASTA/capas/. Abra PASTA/estudio.html no navegador: cada cartão tem
o vídeo, a legenda com botão de copiar, o link pra baixar e o estado. Nada sai do seu computador.
"""
import argparse
import html
import json
import os
import subprocess
from datetime import date

ESTADOS = ["pronto", "programado", "postado"]

CSS = """
:root{--fundo:#f4f4f1;--tinta:#16181d;--suave:rgba(22,24,29,.6);--linha:rgba(22,24,29,.12);--cor:#2552d9;--ok:#1f8a4c;--meio:#b7791f}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,Inter,Segoe UI,sans-serif;background:var(--fundo);color:var(--tinta);padding:36px 18px 80px}
.wrap{max-width:1000px;margin:0 auto}h1{font-size:34px;letter-spacing:-.03em;margin-bottom:6px}.sub{color:var(--suave);margin-bottom:28px}
.card{display:grid;grid-template-columns:220px 1fr;gap:22px;background:#fff;border:1px solid var(--linha);border-radius:18px;padding:18px;margin-bottom:16px}
.card video{width:220px;aspect-ratio:9/16;border-radius:12px;background:#000;display:block}
h2{font-size:20px;letter-spacing:-.01em;margin:2px 0 8px}.meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.tag{font-size:12px;font-weight:600;padding:4px 10px;border-radius:999px;background:#eef0f4;color:var(--suave)}
.tag.pronto{background:#e8f0ff;color:var(--cor)}.tag.programado{background:#fff4e0;color:var(--meio)}.tag.postado{background:#e6f5ec;color:var(--ok)}
.leg{white-space:pre-wrap;font-size:14px;line-height:1.55;background:#f7f7f5;border-radius:10px;padding:12px;margin:6px 0 10px;max-height:220px;overflow:auto}
.acoes{display:flex;gap:8px;flex-wrap:wrap}button,a.bt{font:inherit;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;border:1px solid var(--linha);background:#fff;color:var(--tinta);cursor:pointer;text-decoration:none}
button:hover,a.bt:hover{border-color:var(--cor);color:var(--cor)}.nota{font-size:13px;color:var(--suave);margin-top:8px}
@media(max-width:640px){.card{grid-template-columns:1fr}.card video{width:100%;max-width:300px}}
"""

JS = """
function copiar(id,bt){const t=document.getElementById(id).innerText;navigator.clipboard.writeText(t).then(()=>{const o=bt.innerText;bt.innerText='Copiado';setTimeout(()=>bt.innerText=o,1200)})}
"""


def carregar(pasta):
    p = os.path.join(pasta, "estudio.json")
    return json.load(open(p)) if os.path.exists(p) else {"itens": []}


def salvar(pasta, dados):
    json.dump(dados, open(os.path.join(pasta, "estudio.json"), "w"), ensure_ascii=False, indent=1)


def capa(pasta, arquivo):
    os.makedirs(os.path.join(pasta, "capas"), exist_ok=True)
    destino = os.path.join(pasta, "capas", os.path.splitext(arquivo)[0] + ".jpg")
    if not os.path.exists(destino):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", os.path.join(pasta, arquivo), "-frames:v", "1",
                        "-vf", "scale=540:-2", destino], check=False)
    return os.path.relpath(destino, pasta) if os.path.exists(destino) else None


def varrer(pasta, dados):
    existentes = {i["arquivo"] for i in dados["itens"]}
    for f in sorted(os.listdir(pasta)):
        if f.lower().endswith(".mp4") and f not in existentes:
            dados["itens"].append({"arquivo": f, "titulo": os.path.splitext(f)[0].replace("-", " ").replace("_", " "),
                                   "estado": "pronto", "palavra": "", "legenda_instagram": "", "legenda_tiktok": "",
                                   "nota": "", "adicionado_em": date.today().isoformat()})
    dados["itens"] = [i for i in dados["itens"] if os.path.exists(os.path.join(pasta, i["arquivo"]))]
    for i in dados["itens"]:
        i["capa"] = capa(pasta, i["arquivo"])


def pagina(pasta, dados):
    cards = []
    for k, i in enumerate(dados["itens"]):
        e = html.escape
        legs = ""
        for rede, chave in (("Instagram", "legenda_instagram"), ("TikTok", "legenda_tiktok")):
            if i.get(chave):
                legs += (f'<div class="tag">{rede}</div><div class="leg" id="leg{k}{rede}">{e(i[chave])}</div>'
                         f'<div class="acoes"><button onclick="copiar(\'leg{k}{rede}\',this)">Copiar legenda do {rede}</button></div>')
        poster = f' poster="{e(i["capa"])}"' if i.get("capa") else ""
        palavra = f'<span class="tag">Palavra: {e(i["palavra"])}</span>' if i.get("palavra") else ""
        nota = f'<div class="nota">{e(i["nota"])}</div>' if i.get("nota") else ""
        cards.append(f"""<div class="card"><div><video controls preload="metadata" src="{e(i['arquivo'])}"{poster}></video></div>
<div><h2>{e(i['titulo'])}</h2><div class="meta"><span class="tag {e(i['estado'])}">{e(i['estado'])}</span>{palavra}<span class="tag">{e(i['arquivo'])}</span></div>
{legs}<div class="acoes" style="margin-top:10px"><a class="bt" href="{e(i['arquivo'])}" download>Baixar o vídeo</a></div>{nota}</div></div>""")
    n = len(dados["itens"])
    doc = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Estúdio</title><style>{CSS}</style></head><body><div class="wrap"><h1>Estúdio</h1>
<p class="sub">{n} {'vídeo pronto' if n == 1 else 'vídeos prontos'}. Gerado em {date.today().strftime('%d/%m/%Y')}. Edite o estudio.json e rode o estudio.py de novo pra atualizar.</p>
{''.join(cards) or '<p class="sub">Nenhum .mp4 nesta pasta ainda.</p>'}</div><script>{JS}</script></body></html>"""
    open(os.path.join(pasta, "estudio.html"), "w", encoding="utf-8").write(doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--video", help="arquivo .mp4 dentro da pasta pra atualizar os campos abaixo")
    ap.add_argument("--titulo")
    ap.add_argument("--legenda-instagram")
    ap.add_argument("--legenda-tiktok")
    ap.add_argument("--palavra")
    ap.add_argument("--estado", choices=ESTADOS)
    ap.add_argument("--nota")
    a = ap.parse_args()
    pasta = os.path.abspath(a.pasta)
    dados = carregar(pasta)
    varrer(pasta, dados)
    if a.video:
        item = next((i for i in dados["itens"] if i["arquivo"] == os.path.basename(a.video)), None)
        if not item:
            raise SystemExit(f"{a.video} não está na pasta {pasta}")
        for campo, valor in (("titulo", a.titulo), ("legenda_instagram", a.legenda_instagram), ("legenda_tiktok", a.legenda_tiktok),
                             ("palavra", a.palavra), ("estado", a.estado), ("nota", a.nota)):
            if valor is not None:
                item[campo] = valor
    salvar(pasta, dados)
    pagina(pasta, dados)
    print(f"Estúdio: {os.path.join(pasta, 'estudio.html')}  ({len(dados['itens'])} vídeos)")
    for i in dados["itens"]:
        print(f"  [{i['estado']:10s}] {i['titulo']}  ({i['arquivo']})")


if __name__ == "__main__":
    main()
