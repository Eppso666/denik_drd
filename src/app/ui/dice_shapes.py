"""Kostky v podobě skutečných kostek (podle grafického návrhu): k4 čtyřstěn, k6 krychle, k8 osmistěn,
k10 deltoid, k12 dvanáctistěn, k20 dvacetistěn, k6+ krychle se znaménkem plus, k% dvě desetistěnky.
Tvar je obrázek SVG, číslo uvnitř je běžný text aplikace (stejné písmo jako zbytek)."""
from __future__ import annotations

import flet as ft

_SHAPES = {
    "4": ('<polygon points="50,6 95,88 5,88" fill="url(#g)" stroke="{st}" stroke-width="2.2" stroke-linejoin="round"/>'
          '<path d="M50 6 L50 60 M50 60 L5 88 M50 60 L95 88" stroke="{ln}" stroke-width="1.4" fill="none"/>', (0, .24)),
    "6": ('<path d="M22 20 L78 20 L90 32 L90 88 L34 88 L22 76 Z" fill="url(#g)" stroke="{st}" stroke-width="2.2" '
          'stroke-linejoin="round"/><path d="M22 20 L34 32 L90 32 M34 32 L34 88" stroke="{ln}" stroke-width="1.4" '
          'fill="none"/>', (.12, .18)),
    "8": ('<polygon points="50,4 94,50 50,96 6,50" fill="url(#g)" stroke="{st}" stroke-width="2.2" stroke-linejoin="round"/>'
          '<path d="M6 50 L50 30 L94 50 M50 4 L50 30" stroke="{ln}" stroke-width="1.4" fill="none"/>', (0, .12)),
    "10": ('<polygon points="50,4 94,44 50,96 6,44" fill="url(#g)" stroke="{st}" stroke-width="2.2" stroke-linejoin="round"/>'
           '<path d="M6 44 L28 54 L50 46 L72 54 L94 44 M50 4 L50 46 M28 54 L50 96 L72 54" stroke="{ln}" '
           'stroke-width="1.4" fill="none"/>', (0, .16)),
    "12": ('<polygon points="50,4 94,36 77,90 23,90 6,36" fill="url(#g)" stroke="{st}" stroke-width="2.2" '
           'stroke-linejoin="round"/><polygon points="50,24 72,40 64,68 36,68 28,40" fill="none" stroke="{ln}" '
           'stroke-width="1.4"/><path d="M50 4 L50 24 M94 36 L72 40 M77 90 L64 68 M23 90 L36 68 M6 36 L28 40" '
           'stroke="{ln}" stroke-width="1.4"/>', (0, .06)),
    "20": ('<polygon points="50,3 92,27 92,73 50,97 8,73 8,27" fill="url(#g)" stroke="{st}" stroke-width="2.2" '
           'stroke-linejoin="round"/><polygon points="50,24 76,66 24,66" fill="none" stroke="{ln}" stroke-width="1.4"/>'
           '<path d="M50 3 L50 24 L8 27 M50 24 L92 27 M8 73 L24 66 L8 27 M92 73 L76 66 L92 27 M50 97 L24 66 '
           'M50 97 L76 66" stroke="{ln}" stroke-width="1.2" fill="none"/>', (0, .04)),
}


def kind_of(name: str) -> str:
    """„k20“ → „20“, „3k6“ → „6“, „k6+“ → „6+“, „k%“ → „%“; neznámé → „6“."""
    n = str(name).lower().split("k", 1)[-1]
    if n in ("%", "6+"):
        return n
    digits = "".join(ch for ch in n if ch.isdigit())
    return digits if digits in _SHAPES else "6"


def svg(sides: str, look, sel: bool = False) -> bytes:
    key = "6" if sides == "6+" else ("10" if sides == "%" else sides)
    body = _SHAPES[key][0].format(st=look.orn, ln=look.frame)
    if sides == "%":
        body = (f'<g transform="translate(-14 6) scale(.78)" opacity=".75">{body}</g>'
                f'<g transform="translate(26 14) scale(.78)">{body}</g>')
    if sides == "6+":
        body += (f'<circle cx="80" cy="22" r="11" fill="{look.accent}" stroke="{look.orn}" stroke-width="1.5"/>'
                 '<path d="M80 16 V28 M74 22 H86" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>')
    c1, c2 = (look.accent2, look.accent) if sel else (look.card2, look.bg)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 112 112" width="112" height="112">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
            f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs>{body}</svg>').encode()


def die(app, sides: str, value: str | None = None, size: int = 58, sel: bool = False) -> ft.Control:
    """Tvar kostky; s hodnotou uprostřed (výsledek hodu)."""
    l = app.look
    key = "6" if sides == "6+" else ("10" if sides == "%" else sides)
    dx, dy = _SHAPES[key][1]
    if sides == "%":
        dx, dy = 0, .1
    layers: list[ft.Control] = [ft.Image(src=svg(sides, l, sel), width=size, height=size, fit=ft.BoxFit.CONTAIN)]
    if value not in (None, ""):
        txt = str(value)
        fs = size * (.34 if len(txt) <= 2 else .26) * (.8 if sides == "4" else 1)
        layers.append(ft.Container(
            app.kit.text(txt, size=round(fs), weight=ft.FontWeight.BOLD, head=True, color="#ffffff" if sel else l.ink,
                         align=ft.TextAlign.CENTER),
            alignment=ft.Alignment(dx, dy), width=size, height=size))
    return ft.Container(ft.Stack(layers, width=size, height=size),
                        shadow=[ft.BoxShadow(blur_radius=14, color=l.glow)] if sel else None,
                        border_radius=ft.BorderRadius.all(size))
