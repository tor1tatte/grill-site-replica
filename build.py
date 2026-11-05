#!/usr/bin/env python3
"""Static site generator for the grill-site clone.

Reads  src/content.json + replica/design/tokens.json
Writes site/  (HTML pages, assets/css, assets/js, assets/img/*.svg, sitemap.xml, robots.txt)

Usage:  python3 build.py
"""
import argparse
import html
import json
import pathlib
import random
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
_ap = argparse.ArgumentParser(description="Build the static site")
_ap.add_argument("--out", default="site", help="output folder (default: site)")
_ap.add_argument("--base", default="", help="URL path prefix, e.g. /my-repo for GitHub Pages")
_ap.add_argument("--domain", default="", help="public origin incl. base path, used for canonical / og / sitemap")
_ap.add_argument("--demo", action="store_true", help="demo build: banner, noindex, forms do not send")
ARGS = _ap.parse_args()
OUT = ROOT / ARGS.out
BASE = ARGS.base.rstrip("/")
C = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
T = json.loads((ROOT / "replica/design/tokens.json").read_text(encoding="utf-8"))
B = C["brand"]
if ARGS.domain:
    B["domain"] = ARGS.domain
F = C["form"]
CATS = C["categories"]
PH_FILE = SRC / "photos.json"
PH = json.loads(PH_FILE.read_text(encoding="utf-8")) if PH_FILE.exists() else None


def esc(s):
    return html.escape(str(s), quote=True)


def rub(n):
    return f"{n:,}".replace(",", " ") + " ₽"


# ---------------------------------------------------------------- tokens.css
def tokens_css():
    L = [":root{"]
    for k, v in T["color"].items():
        L.append(f"  --c-{k}:{v};")
    for k, v in T["type"].items():
        L.append(f"  --fs-{k}:{v['size'] / 16:.4g}rem;--lh-{k}:{v['line'] / 16:.4g}rem;--fw-{k}:{v['weight']};")
    L.append(f"  --font-display:{T['font']['display']};")
    L.append(f"  --font-sans:{T['font']['sans']};")
    for i, v in enumerate(T["space"]):
        L.append(f"  --s-{i}:{v / 16:.4g}rem;")
    for k, v in T["radius"].items():
        L.append(f"  --r-{k}:{v}px;")
    for k, v in T["shadow"].items():
        L.append(f"  --sh-{k}:{v};")
    for k, v in T["motion"].items():
        L.append(f"  --t-{k}:{v};" if k != "ease" else f"  --ease:{v};")
    L.append(f"  --max:{T['layout']['max']}px;--header:{T['layout']['header']}px;")
    L.append("}")
    return "\n".join(L) + "\n"


# ------------------------------------------------------- placeholder pictures
PALS = [
    ("#223226", "#0d1510", "#2c2b27"),
    ("#2b2338", "#110d19", "#2a2724"),
    ("#3a2c1e", "#160f09", "#2c2926"),
    ("#1e2f3a", "#0b1217", "#262829"),
    ("#37211f", "#140b0b", "#292626"),
]
IMG_DIR = OUT / "assets" / "img"
_made = set()


def scene(seed, variant=0, wide=None):
    """Original placeholder illustration: a stylised outdoor grill unit at dusk.
    wide=None -> 1200x900 (cards); wide='l'/'r' -> 1800x720 banner with the unit on that side."""
    W, H = (1200, 900) if not wide else (1800, 720)
    k = H / 900
    name = f"{seed}-{variant}{'-w' + wide if wide else ''}.svg"
    if name in _made:
        return "/assets/img/" + name
    r = random.Random(f"{seed}:{variant}")
    top, bot, ground = r.choice(PALS)
    unit_w = r.randint(520, 760)
    x0 = (1200 - unit_w) // 2 + r.randint(-60, 60)
    gy = 640  # ground line, in the 1200x900 design space
    ch = r.randint(190, 240)  # cabinet height
    cy = gy - ch
    doors = r.choice([2, 3, 4])
    wood = r.choice(["#8a5632", "#6e4a31", "#9a6a3c", "#3b3b3e"])
    steel = "#c7ccd1"
    hood = r.random() < 0.7
    dx = 0.0
    if wide:
        dx = (W * (0.27 if wide == "l" else 0.73)) - 600 * k
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">')
    p.append(f'<defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient>')
    p.append('<linearGradient id="h" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff8a3d" stop-opacity="0"/><stop offset="1" stop-color="#ff8a3d" stop-opacity=".22"/></linearGradient>')
    p.append('<radialGradient id="g" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffb347" stop-opacity=".95"/><stop offset="1" stop-color="#ff6a00" stop-opacity="0"/></radialGradient>')
    p.append('<radialGradient id="l" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffe2a8" stop-opacity=".9"/><stop offset="1" stop-color="#ffe2a8" stop-opacity="0"/></radialGradient></defs>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#s)"/>')
    gyc = gy * k
    p.append(f'<rect y="{gyc * 0.55:.0f}" width="{W}" height="{gyc * 0.45:.0f}" fill="url(#h)"/>')
    for _ in range(5 if not wide else 9):
        tx = r.randint(0, W)
        p.append(f'<ellipse cx="{tx}" cy="{gyc - 60 * k:.0f}" rx="{r.randint(110, 200) * k:.0f}" ry="{r.randint(180, 320) * k:.0f}" fill="#000" opacity=".22"/>')
    p.append(f'<rect y="{gyc:.0f}" width="{W}" height="{H - gyc:.0f}" fill="{ground}"/>')
    for i in range(0, W, 120):
        p.append(f'<rect x="{i}" y="{gyc:.0f}" width="2" height="{H - gyc:.0f}" fill="#000" opacity=".25"/>')
    p.append(f'<g transform="translate({dx:.0f},0) scale({k:.4f})">')
    # wall panel
    p.append(f'<rect x="{x0 - 30}" y="{cy - 330}" width="{unit_w + 60}" height="{330 + ch}" fill="#000" opacity=".28"/>')
    # string lights
    for i in range(r.randint(4, 8)):
        lx = x0 + r.randint(0, unit_w)
        ly = cy - r.randint(240, 320)
        p.append(f'<circle cx="{lx}" cy="{ly}" r="46" fill="url(#l)"/><circle cx="{lx}" cy="{ly}" r="5" fill="#fff4d6"/>')
    # hood
    if hood:
        p.append(f'<path d="M{x0 + 40} {cy - 210} L{x0 + unit_w - 40} {cy - 210} L{x0 + unit_w - 100} {cy - 330} L{x0 + 100} {cy - 330} Z" fill="#111" opacity=".92"/>')
        p.append(f'<rect x="{x0 + 40}" y="{cy - 214}" width="{unit_w - 80}" height="8" fill="#000"/>')
    # cabinet
    p.append(f'<rect x="{x0}" y="{cy}" width="{unit_w}" height="{ch}" fill="#17181a"/>')
    dw = (unit_w - 40) / doors
    for i in range(doors):
        ddx = x0 + 20 + i * dw
        p.append(f'<rect x="{ddx + 4:.0f}" y="{cy + 18}" width="{dw - 8:.0f}" height="{ch - 36}" rx="4" fill="{wood}"/>')
        p.append(f'<rect x="{ddx + dw / 2 - 3:.0f}" y="{cy + 34}" width="6" height="{ch * 0.38:.0f}" rx="3" fill="{steel}" opacity=".85"/>')
    # countertop
    p.append(f'<rect x="{x0 - 14}" y="{cy - 22}" width="{unit_w + 28}" height="24" rx="4" fill="#2d2e31"/>')
    # grill
    gx = x0 + unit_w * r.choice([0.3, 0.45, 0.6])
    gw = r.randint(170, 230)
    p.append(f'<ellipse cx="{gx:.0f}" cy="{cy - 34}" rx="{gw * 0.95:.0f}" ry="62" fill="url(#g)" opacity=".75"/>')
    p.append(f'<rect x="{gx - gw / 2:.0f}" y="{cy - 78}" width="{gw}" height="56" rx="8" fill="#0f0f10" stroke="{steel}" stroke-opacity=".5"/>')
    for i in range(5):
        p.append(f'<rect x="{gx - gw / 2 + 14 + i * (gw - 28) / 4 - 2:.0f}" y="{cy - 70}" width="4" height="36" fill="{steel}" opacity=".7"/>')
    if r.random() < 0.6:
        sx = x0 + 8
        for i in range(3):
            for j in range(3 - i):
                p.append(f'<circle cx="{sx + 16 + j * 28 + i * 14}" cy="{gy - 14 - i * 24}" r="13" fill="#7a4a24" stroke="#3b2210"/>')
    p.append("</g></svg>")
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    (IMG_DIR / name).write_text("".join(p), encoding="utf-8")
    _made.add(name)
    return "/assets/img/" + name


def img_illustration(seed, alt, variant=0, cls="", eager=False, wide=None):
    src = scene(seed, variant, wide)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    w, h = (1800, 720) if wide else (1200, 900)
    return f'<img{c} src="{src}" alt="{esc(alt)}" width="{w}" height="{h}" {load} decoding="async">'


_assigned = {}
_pool_pos = {}
_use_count = {}
_used_files = set()
FOCUS = ["50% 50%", "30% 45%", "70% 55%", "50% 40%"]
SIZES = {"sm": 640, "md": 1200, "lg": 1600}


def pick(seed, variant=0):
    """Photo key for (seed, variant): pinned in 'fixed', else handed out in order from the seed's pool."""
    k = (seed, variant)
    if k in _assigned:
        return _assigned[k]
    key = None
    if variant == 0 and seed in PH["fixed"]:
        key = PH["fixed"][seed]
    else:
        m = re.match(r"^([a-z]+)\d+$", seed)
        prefix = m.group(1) if m else None
        # a pool can be given per slide ("t@0", "t@1"); otherwise slide 0 walks the pool forwards
        # and later slides walk it backwards, so first pictures stay unique and a card never repeats itself
        pool = (PH["pools"].get("%s@%d" % (prefix, variant)) or PH["pools"].get(prefix)) if prefix else None
        if pool:
            slot = (prefix, variant)
            i = _pool_pos.get(slot, 0)
            _pool_pos[slot] = i + 1
            explicit = ("%s@%d" % (prefix, variant)) in PH["pools"]
            key = pool[i % len(pool)] if (variant == 0 or explicit) else pool[(len(pool) - 1 - i) % len(pool)]
    _assigned[k] = key
    return key


def photo_url(key, sz):
    _used_files.add((key, SIZES[sz]))
    return "/assets/photos/%s-%d.jpg" % (key, SIZES[sz])


def view_src(seed, variant=0):
    key = pick(seed, variant) if PH else None
    return photo_url(key, "lg") if key else scene(seed, variant)


def og_url(seed):
    key = pick(seed, 0) if PH else None
    return photo_url(key, "lg") if key else scene(seed, 0)


def img(seed, alt, variant=0, cls="", eager=False, wide=None, sz="md"):
    key = pick(seed, variant) if PH else None
    if not key:
        return img_illustration(seed, alt, variant, cls, eager, wide)
    ph = PH["photos"][key]
    w = SIZES[sz]
    h = round(w * ph["h"] / ph["w"])
    n = _use_count.get(key, 0)
    _use_count[key] = n + 1
    style = "" if wide else ' style="object-position:%s"' % FOCUS[n % len(FOCUS)]
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    c = ' class="%s"' % cls if cls else ""
    text = "" if alt == "" else ph["alt"]
    return '<img%s src="%s" alt="%s" width="%d" height="%d" %s decoding="async"%s>' % (
        c, photo_url(key, sz), esc(text), w, h, load, style)


# -------------------------------------------------------------------- icons
def ico(name, cls="ico"):
    d = {
        "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
        "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
        "up": '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
        "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
        "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
        "down": '<path d="m6 9 6 6 6-6"/>',
        "left": '<path d="m15 18-6-6 6-6"/>',
        "right": '<path d="m9 18 6-6-6-6"/>',
        "menu": '<path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/>',
        "flame": '<path d="M12 2c1 4 5 6 5 11a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-4-1-6 1-10z"/>',
        "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
        "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    }[name]
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{d}</svg>'


def logo_html():
    n = B["name"]
    mid = len(n) // 2
    return (f'<a class="logo" href="/" aria-label="{esc(n)} — на главную">{ico("flame", "logo__mark")}'
            f'<span class="logo__t">{esc(n[:mid])}<b>{esc(n[mid:])}</b></span></a>')


# ------------------------------------------------------------------ chrome
def header_html():
    subs = "".join(f'<li><a href="/{CATS[k]["slug"]}/">{esc(CATS[k]["short"])}</a></li>' for k in C["nav"][2]["sub"])
    items = []
    for n in C["nav"]:
        if "sub" in n:
            items.append(
                f'<li class="has-sub"><button type="button" class="nav__btn" aria-expanded="false" aria-controls="submenu">{esc(n["label"])}{ico("down", "ico ico--s")}</button>'
                f'<ul class="sub" id="submenu">{subs}</ul></li>')
        else:
            items.append(f'<li><a href="{n["href"]}">{esc(n["label"])}</a></li>')
    return f'''<header class="hdr"><div class="wrap hdr__in">
{logo_html()}
<nav class="nav" id="nav" aria-label="Основное меню"><ul>{"".join(items)}</ul></nav>
<div class="hdr__soc"><a class="soc" href="{esc(B["tg"])}" aria-label="Telegram" rel="noopener">{ico("send")}</a><a class="soc" href="{esc(B["vk"])}" aria-label="ВКонтакте" rel="noopener"><span aria-hidden="true">VK</span></a></div>
<div class="hdr__ph"><a href="tel:{esc(B["phone_tel"])}">{esc(B["phone"])}</a><a class="hdr__mail" href="mailto:{esc(B["email"])}">{esc(B["email"])}</a></div>
<button class="burger" type="button" aria-label="Открыть меню" aria-expanded="false" aria-controls="nav">{ico("menu")}</button>
</div></header>'''


def footer_html():
    links = "".join(f'<li><a href="{n["href"]}">{esc(n["label"])}</a></li>' for n in C["nav"] if "sub" not in n)
    s = C["contact"]
    return f'''<footer class="ftr"><div class="wrap ftr__in">
<div><p class="ftr__h">Контакты</p><p><a href="tel:{esc(B["phone_tel"])}">{esc(B["phone"])}</a></p><p><a href="mailto:{esc(B["email"])}">{esc(B["email"])}</a></p><p>{esc(B["hours"])}</p></div>
<div><p class="ftr__h">{esc(s["sites"][0]["h"])}</p><p>{esc(s["sites"][0]["addr"])}</p><p class="ftr__h ftr__h--2">{esc(s["sites"][1]["h"])}</p><p>{esc(s["sites"][1]["addr"])}</p></div>
<div><p class="ftr__h">Разделы</p><ul class="ftr__links">{links}</ul></div>
<div><p class="ftr__h">Мы в сети</p><p><a href="{esc(B["tg"])}" rel="noopener">Telegram</a></p><p><a href="{esc(B["vk"])}" rel="noopener">ВКонтакте</a></p></div>
</div>
<div class="wrap ftr__legal"><p>{esc(B["legal"])}</p><p>{esc(B["copyright"])} · <a href="/privacy/">Положение</a> · <a href="/consent/">Согласие</a> · <a href="/credits/">Авторы фото</a></p></div></footer>'''


def dock_html():
    return f'''<aside class="dock" aria-label="Быстрая связь">
<button class="dock__t" type="button" aria-expanded="true" aria-label="Свернуть панель связи">{ico("x")}</button>
<div class="dock__list">
<a class="dock__b" href="{esc(B["tg"])}" rel="noopener">{ico("send")}<span>Telegram</span></a>
<a class="dock__b" href="{esc(B["vk"])}" rel="noopener"><b aria-hidden="true">VK</b><span>ВКонтакте</span></a>
<a class="dock__b" href="tel:{esc(B["phone_tel"])}">{ico("phone")}<span>Позвонить</span></a>
<a class="dock__b" href="#top" data-top>{ico("up")}<span>Наверх</span></a>
</div></aside>'''


def lead_fields(extra_email=False):
    return f'''<input type="hidden" name="source" value=""><input type="hidden" name="product" value="">
<div class="hp" aria-hidden="true"><label>Не заполняйте <input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
<label class="fld"><span>{esc(F["name"])}</span><input type="text" name="name" autocomplete="name" maxlength="80"></label>
<label class="fld"><span>{esc(F["phone"])}<i aria-hidden="true">*</i></span><input type="tel" name="phone" autocomplete="tel" inputmode="tel" placeholder="+7 (___) ___-__-__" required aria-describedby="e-phone"></label>
<label class="fld{'' if extra_email else ' fld--catalog'}" {'' if extra_email else 'data-catalog-only hidden'}><span>{esc(F["email"])}</span><input type="email" name="email" autocomplete="email" maxlength="120"></label>
<label class="chk"><input type="checkbox" name="consent" required><span>{F["consent"]}</span></label>
<p class="err" role="alert" aria-live="assertive"></p>
<button class="btn btn--block" type="submit"><span class="btn__t">{esc(F["send"])}</span></button>'''


def modals_html():
    return f'''<dialog class="modal" id="lead" aria-labelledby="lead-title"><div class="modal__box">
<button class="modal__x" type="button" data-close aria-label="{esc(F["close"])}">{ico("x")}</button>
<h2 id="lead-title" class="modal__h">{esc(F["title_order"])}</h2><p class="modal__prod" id="lead-prod"></p>
<form data-lead novalidate>{lead_fields(False)}</form>
<div class="ok" hidden><h2 class="modal__h">{esc(F["ok_title"])}</h2><p class="ok__t">{esc(F["ok_text"])}</p><p class="ok__cat" hidden>{esc(F["ok_catalog"])}</p><button class="btn" type="button" data-close>{esc(F["close"])}</button></div>
</div></dialog>
<dialog class="modal modal--wide" id="viewer" aria-label="Просмотр"><div class="modal__box modal__box--wide">
<button class="modal__x" type="button" data-close aria-label="{esc(F["close"])}">{ico("x")}</button>
<div class="viewer" id="viewer-body"></div></div></dialog>'''


def play_btn():
    return f'<span class="play" aria-hidden="true">{ico("play")}</span>'


# ------------------------------------------------------------------- layout
def layout(path, title, desc, body, *, og_seed="hero-home", ld=None, cls=""):
    canon = B["domain"].rstrip("/") + ("/" + path.strip("/") + "/" if path.strip("/") else "/")
    og = B["domain"].rstrip("/") + og_url(og_seed)
    jl = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    doc = f'''<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}"><meta property="og:image" content="{esc(og)}">
<meta name="theme-color" content="{T["color"]["surface-dark"]}">
<meta name="lead-endpoint" content="/api/lead">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Crect width='24' height='24' rx='5' fill='%23141414'/%3E%3Cpath d='M12 3c1 4 5 6 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3 0-4-1-6 1-9z' fill='%23c2410c'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Oswald:wght@500;600&display=swap">
<link rel="stylesheet" href="/assets/css/tokens.css"><link rel="stylesheet" href="/assets/css/style.css">
{jl}</head>
<body class="{cls}" id="top"><a class="skip" href="#main">К содержимому</a>
{header_html()}
<main id="main">{body}</main>
{footer_html()}
{dock_html()}
{modals_html()}
<script src="/assets/js/app.js" defer></script>
</body></html>'''
    if ARGS.demo:
        doc = doc.replace('<meta name="lead-endpoint" content="/api/lead">', '<meta name="lead-endpoint" content="">')
        doc = doc.replace("</head>", '<meta name="robots" content="noindex, nofollow"></head>', 1)
        doc = doc.replace('<a class="skip" href="#main">К содержимому</a>', '<a class="skip" href="#main">К содержимому</a><div class="demo-bar">Демонстрационная версия: тексты, цены и контакты — примеры, фото — стоковые</div>', 1)
    if BASE:
        doc = re.sub(r'(href|src|data-view-img)="/', r'\1="' + BASE + "/", doc)
    d = OUT / path.strip("/") if path.strip("/") else OUT
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(doc, encoding="utf-8")


# -------------------------------------------------------------- components
def section_head(label, h2, lead="", accent=""):
    hh = esc(h2)
    if accent and accent in hh:
        hh = hh.replace(accent, f"<em>{accent}</em>", 1)
    lead_html = f'<p class="sec__lead">{esc(lead)}</p>' if lead else ""
    lab = f'<p class="sec__label"><span>{esc(label)}</span></p>' if label else ""
    return f'{lab}<h2 class="sec__h">{hh}</h2>{lead_html}'


def accordion(g, key, extra=None):
    items = list(g.get(key, [])) + list(extra or [])
    if not items:
        return ""
    lis = "".join(f"<li>{esc(i)}</li>" for i in items)
    return f'<details class="acc"><summary>{esc(C["group_labels"][key])}</summary><ul>{lis}</ul></details>'


def product_card(cat, it):
    prefix = it.get("prefix", cat["prefix"])
    title = f'{esc(prefix)} <span>«{esc(it["name"])}»</span>' if prefix else f'<span>{esc(it["name"])}</span>'
    g = C["presets"].get(it.get("groups", ""), {})
    dims = "".join(f"<li>{esc(d)}</li>" for d in it["dims"])
    nm = it["name"]
    slides = "".join(
        '<div class="slide%s" data-i="%d">%s</div>' % (
            " is-on" if v == 0 else "", v,
            img(it["seed"], "%s, вид %d (иллюстрация-заглушка)" % (nm, v + 1), v))
        for v in range(2))
    thumbs = "".join(
        '<button type="button" class="thumb%s" data-go="%d" aria-label="Показать вид %d">%s</button>' % (
            " is-on" if v == 0 else "", v, v + 1, img(it["seed"], "", v, sz="sm"))
        for v in range(2))
    order_name = (prefix + " «" + nm + "»") if prefix else nm
    accs = accordion(g, "zones") + accordion(g, "func", it.get("extra_func")) + accordion(g, "services")
    return f'''<article class="pcard" id="{esc(it["id"])}">
<h2 class="pcard__title">{title}</h2>
<div class="slider pcard__media" data-slider><div class="slider__stage">{slides}
<button type="button" class="slider__nav slider__nav--l" data-dir="-1" aria-label="Предыдущий вид">{ico("left")}</button>
<button type="button" class="slider__nav slider__nav--r" data-dir="1" aria-label="Следующий вид">{ico("right")}</button></div>
<div class="slider__thumbs">{thumbs}</div></div>
<div class="pcard__info"><h3 class="pcard__h">{esc(C["info_label"])}</h3><ul class="pcard__dims">{dims}</ul>
<div class="accs">{accs}</div><p class="pcard__note">{esc(C["card_note"])}</p>
<div class="pcard__buy"><p class="price"><small>{esc(C["price_label"])}</small><b>{rub(it["price"])}</b></p>
<button type="button" class="btn" data-lead-open="order" data-product="{esc(order_name)}">{esc(C["order_label"])}</button></div></div>
</article>'''


def module_card(m):
    return f'''<article class="mcard" id="{esc(m["id"])}">{img(m["seed"], m["name"] + " (иллюстрация-заглушка)", sz="sm")}
<div class="mcard__b"><h3>{esc(m["name"])}</h3><p>{esc(m["dims"])}</p>
<div class="mcard__buy"><b>{rub(m["price"])}</b><button type="button" class="btn btn--sm" data-lead-open="order" data-product="{esc(m["name"])}">{esc(C["order_label"])}</button></div></div></article>'''


def cat_hero(h, eager=True):
    return f'''<section class="chero">{img(h["seed"], h["h1"], 0, "chero__bg", eager, "l")}<div class="chero__shade"></div>
<div class="chero__in"><h1>{esc(h["h1"])}</h1><p>{esc(h["lead"])}</p><button type="button" class="btn" data-lead-open="calc">{esc(h["cta"])}</button></div></section>'''


# --------------------------------------------------------------------- pages
def page_home():
    h = C["home"]
    hero = h["hero"]
    badges = "".join(f'<li>{ico("flame", "ico ico--acc")}<span>{esc(b)}</span></li>' for b in hero["badges"])
    stats = "".join(
        f'<div class="stat{" stat--acc" if s.get("accent") else ""}"><b>{esc(s["num"])}</b><span>{esc(s["cap"])}</span></div>' for s in h["about"]["stats"])
    tiles = []
    for t in C["gallery_tiles"]:
        sp = t["span"]
        if sp.startswith("video"):
            tiles.append(f'<button type="button" class="tile tile--{sp}" data-view-video="" aria-label="Смотреть видео">{img(t["seed"], "Кадр из видео (заглушка)", 0, "", False, None, "md")}{play_btn()}</button>')
        else:
            tiles.append(f'<button type="button" class="tile" data-view-img="{view_src(t["seed"])}" aria-label="Открыть фото крупнее">{img(t["seed"], "Фото проекта (заглушка)", sz="sm")}</button>')
    show = []
    for i, s in enumerate(C["showcase"]):
        c = CATS[s["cat"]]
        stamp = '<span class="stamp" aria-hidden="true">PREMIUM</span>' if s.get("premium") else ""
        show.append(f'''<article class="show{" show--alt" if i % 2 else ""}">{img(s["seed"], s["title"] + " (иллюстрация-заглушка)", 0, "", False, "r" if i % 2 else "l")}<div class="show__shade"></div>{stamp}
<div class="show__in"><p class="show__k">{esc(s["kicker"])}</p><h3 class="show__t">{esc(s["title"])}</h3><p class="show__f">{esc(s["flag"])}</p><p class="show__d">{esc(s["text"])}</p>
<div class="show__btns"><a class="btn" href="/{c["slug"]}/">Подробнее</a><a class="btn btn--ghost" href="/blog/">Смотреть видео {ico("play", "ico ico--s")}</a></div></div></article>''')
    steps = "".join(f'<li class="step"><span class="step__n">{i + 1}</span><h3>{esc(s["t"])}</h3><p>{esc(s["d"])}</p></li>' for i, s in enumerate(h["process"]["steps"]))
    people = "".join(f'<li class="person"><span class="person__av">{ico("user", "ico ico--xl")}</span><b>{esc(p["name"])}</b><span>{esc(p["role"])}</span></li>' for p in h["team"]["people"])
    body = f'''
<section class="hero">{img("hero-home", "Гриль-зона на участке (иллюстрация-заглушка)", 0, "hero__bg", True, "r", "lg")}<div class="hero__shade"></div>
<div class="wrap hero__in"><h1 class="hero__h">{hero["h1"]}</h1><p class="hero__lead">{esc(hero["lead"])}</p><button type="button" class="btn btn--lg" data-lead-open="calc">{esc(hero["cta"])}</button></div>
<ul class="wrap badges">{badges}</ul></section>
<section class="sec" id="about"><div class="wrap sec__c">{section_head(h["about"]["label"], h["about"]["h2"], h["about"]["lead"], "десяти лет")}<div class="stats">{stats}</div></div></section>
<section class="sec sec--grey" id="projects"><div class="wrap sec__c">{section_head(h["gallery"]["label"], h["gallery"]["h2"], h["gallery"]["lead"], "увидеть")}<div class="mosaic">{"".join(tiles)}</div><p class="sec__cta"><a class="btn" href="/portfolio/">{esc(h["gallery"]["more"])}</a></p></div></section>
<section class="sec" id="models"><div class="wrap sec__c">{section_head(h["models"]["label"], h["models"]["h2"], h["models"]["lead"], "гриль-зону")}<p class="sec__cta"><button type="button" class="btn" data-lead-open="catalog">{esc(h["models"]["catalog_btn"])}</button></p>
<div class="shows">{"".join(show)}</div></div></section>
<section class="ask"><div class="wrap ask__in"><div><h2>{esc(h["ask"]["h2"])}</h2><p>{esc(h["ask"]["lead"])}</p></div><button type="button" class="btn btn--lg" data-lead-open="callback">{esc(h["ask"]["cta"])}</button></div></section>
<section class="sec" id="process"><div class="wrap sec__c">{section_head(h["process"]["label"], h["process"]["h2"], "", "под ключ")}<ol class="steps">{steps}</ol></div></section>
<section class="sec sec--grey" id="team"><div class="wrap sec__c">{section_head(h["team"]["label"], h["team"]["h2"], h["team"]["lead"], "своего дела")}<ul class="people">{people}</ul></div></section>
<section class="consult" id="consult"><div class="wrap consult__in"><div><h2>{esc(h["consult"]["h2"])}</h2><p>{esc(h["consult"]["lead"])}</p></div>
<form class="consult__form" data-lead data-source="consult" novalidate>{lead_fields(True).replace(esc(F["send"]), esc(h["consult"]["cta"]))}</form>
<div class="ok ok--inline" hidden><h3>{esc(F["ok_title"])}</h3><p>{esc(F["ok_text"])}</p></div></div></section>'''
    ld = {"@context": "https://schema.org", "@type": "Organization", "name": B["name"], "url": B["domain"], "telephone": B["phone_tel"], "email": B["email"]}
    layout("", h["title"], h["description"], body, og_seed="hero-home", ld=ld, cls="home")


def page_category(key):
    c = CATS[key]
    cards = "".join(product_card(c, it) for it in c["items"])
    extra = ""
    if c.get("modules"):
        extra = f'<section class="wrap mods"><h2 class="sec__h">{esc(c["modules_title"])}</h2><div class="mgrid">{"".join(module_card(m) for m in c["modules"])}</div></section>'
    body = f'{cat_hero(c["hero"])}<section class="wrap pcards">{cards}</section>{extra}'
    layout(c["slug"], c["title"], c["description"], body, og_seed=c["hero"]["seed"], cls="cat")


def page_portfolio():
    p = C["portfolio"]
    cards = []
    for it in p["items"]:
        if it.get("video"):
            media = f'<button type="button" class="pf__media" data-view-video="" aria-label="Смотреть видео: {esc(it["title"])}">{img(it["seed"], it["title"] + " (заглушка)", sz="sm")}{play_btn()}</button>'
        else:
            media = f'<button type="button" class="pf__media" data-view-img="{view_src(it["seed"])}" aria-label="Открыть фото крупнее: {esc(it["title"])}">{img(it["seed"], it["title"] + " (заглушка)", sz="sm")}</button>'
        cards.append(f'<article class="pf">{media}<div class="pf__b"><h3>{esc(it["title"])}</h3><p>{esc(it["spec"])}</p><b>{rub(it["price"])}</b></div></article>')
    body = f'<section class="wrap page"><h1 class="page__h">{esc(p["h1"])}</h1><p class="page__lead">{esc(p["lead"])}</p><h2 class="sec__label sec__label--l"><span>{esc(p["label"])}</span></h2><div class="pfgrid">{"".join(cards)}</div><p class="sec__cta"><button type="button" class="btn" data-lead-open="calc">Хочу такой же проект</button></p></section>'
    layout("portfolio", p["title"], p["description"], body, og_seed="pf1", cls="inner")


def page_blog():
    b = C["blog"]
    cards = "".join(
        f'<article class="vid"><button type="button" class="vid__media" data-view-video="{esc(v["url"])}" aria-label="Смотреть: {esc(v["title"])}">{img(v["seed"], v["title"] + " (заглушка)", sz="sm")}{play_btn()}</button><h3>{esc(v["title"])}</h3></article>'
        for v in b["videos"])
    body = f'<section class="wrap page"><h1 class="page__h">{esc(b["h1"])}</h1><p class="page__lead">{esc(b["lead"])}</p><div class="vgrid">{cards}</div></section>'
    layout("blog", b["title"], b["description"], body, og_seed="v1", cls="inner")


def page_partner():
    p = C["partner"]
    blocks = []
    for blk in p["blocks"]:
        parts = [f'<h2>{esc(blk["h"])}</h2>']
        parts += [f"<p>{esc(t)}</p>" for t in blk.get("p", [])]
        if blk.get("list"):
            parts.append("<ul>" + "".join(f"<li>{esc(i)}</li>" for i in blk["list"]) + "</ul>")
        if blk.get("steps"):
            parts.append('<ol class="nlist">' + "".join(f"<li>{esc(i)}</li>" for i in blk["steps"]) + "</ol>")
        blocks.append(f'<section class="prose">{"".join(parts)}</section>')
    body = f'''<section class="wrap page"><h1 class="page__h">{esc(p["h1"])}</h1><p class="page__lead">{esc(p["lead"])}</p>
<div class="prose-grid">{"".join(blocks)}</div>
<aside class="callbox"><h2>{esc(p["contact_h"])}</h2><p><a href="tel:{esc(C["contact"]["phones"][3]["href"])}">{esc(C["contact"]["phones"][3]["tel"])}</a> · <a href="mailto:{esc(B["email"])}">{esc(B["email"])}</a></p><p>{esc(p["contact_note"])}</p></aside></section>'''
    layout("partner", p["title"], p["description"], body, og_seed="hero-zone", cls="inner")


def page_contact():
    k = C["contact"]
    sites = "".join(f'<section class="addr"><h2>{esc(s["h"])}</h2><p>{esc(s["addr"])}</p></section>' for s in k["sites"])
    phones = "".join(f'<li><span>{esc(p["label"])}</span><a href="tel:{esc(p["href"])}">{esc(p["tel"])}</a></li>' for p in k["phones"])
    body = f'''<section class="wrap page"><h1 class="page__h">{esc(k["h1"])}</h1><div class="addrs">{sites}</div>
<ul class="phones">{phones}<li><span>E-mail</span><a href="mailto:{esc(B["email"])}">{esc(B["email"])}</a></li><li><span>Часы работы</span><b>{esc(B["hours"])}</b></li></ul></section>'''
    layout("contact", k["title"], k["description"], body, og_seed="hero-tub", cls="inner")


def page_legal(key, slug):
    l = C["legal"][key]
    paras = "".join(f"<p>{esc(t)}</p>" for t in l["body"])
    body = f'<section class="wrap page page--narrow"><h1 class="page__h">{esc(l["title"])}</h1><div class="prose">{paras}</div></section>'
    layout(slug, l["title"] + " — " + B["name"], l["title"], body, cls="inner")


def page_credits():
    rows = []
    for key in sorted(k for (k, _w) in {(k, 0) for (k, _w) in _used_files}):
        p = PH["photos"][key]
        who = ('<a href="%s" rel="noopener">%s</a>' % (esc(p["author_url"]), esc(p["author"]))) if p["author"] else "автор не указан"
        rows.append('<li><a href="%s" rel="noopener">%s</a><span>%s · %s</span></li>' % (esc(p["page"]), esc(p["alt"]), who, esc(p["source"])))
    body = (
        '<section class="wrap page page--narrow"><h1 class="page__h">Авторы фотографий</h1>'
        '<p class="page__lead">Фотографии на сайте — иллюстративные стоковые снимки с бесплатными лицензиями '
        '(<a href="https://unsplash.com/license" rel="noopener">Unsplash License</a>, '
        '<a href="https://www.pexels.com/license/" rel="noopener">Pexels License</a>). '
        'На них не обязательно изображены изделия компании: перед запуском замените их на собственные фотографии.</p>'
        '<ul class="credits">%s</ul></section>' % "".join(rows))
    layout("credits", "Авторы фотографий — " + B["name"], "Источники и авторы стоковых фотографий сайта.", body, cls="inner")


# --------------------------------------------------------------------- main
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets" / "css").mkdir(parents=True)
    (OUT / "assets" / "js").mkdir(parents=True)
    (OUT / "assets" / "css" / "tokens.css").write_text(tokens_css(), encoding="utf-8")
    shutil.copy(SRC / "style.css", OUT / "assets" / "css" / "style.css")
    shutil.copy(SRC / "app.js", OUT / "assets" / "js" / "app.js")

    page_home()
    for k in CATS:
        page_category(k)
    page_portfolio()
    page_blog()
    page_partner()
    page_contact()
    page_legal("privacy", "privacy")
    page_legal("consent", "consent")
    if PH:
        page_credits()
        for key, w in sorted(_used_files):
            dst = OUT / "assets" / "photos"
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy(SRC / "photos" / ("%s-%d.jpg" % (key, w)), dst / ("%s-%d.jpg" % (key, w)))

    urls = ["/"] + [f"/{CATS[k]['slug']}/" for k in CATS] + ["/portfolio/", "/blog/", "/partner/", "/contact/", "/privacy/", "/consent/"] + (["/credits/"] if PH else [])
    base = B["domain"].rstrip("/")
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{base}{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    if ARGS.demo:
        (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    if BASE:
        (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"built {len(urls)} pages, {len(_made)} illustrations, {len(_used_files)} photo files -> {OUT}")


if __name__ == "__main__":
    main()
