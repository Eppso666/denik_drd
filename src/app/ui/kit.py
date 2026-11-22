"""Malá sada stavebních prvků UI, které se přizpůsobí vzhledu zvolené hry."""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from ..theme import Look


class Kit:
    def __init__(self, look: Look, head_font: str | None):
        self.l = look
        self.hf = head_font

    # --- text ---------------------------------------------------------------
    def text(self, value, size: float = 15, weight=None, color: str | None = None, head: bool = False,
             italic: bool = False, align=None, expand=None, max_lines=None) -> ft.Text:
        return ft.Text(
            str(value), size=size, weight=weight, color=color or self.l.ink, italic=italic,
            font_family=self.hf if head else None, text_align=align, expand=expand, max_lines=max_lines,
            overflow=ft.TextOverflow.ELLIPSIS if max_lines else None,
        )

    def muted(self, value, size: float = 13, **kw) -> ft.Text:
        kw.setdefault("color", self.l.muted)
        return self.text(value, size=size, **kw)

    def title(self, value, size: float = 24) -> ft.Text:
        return self.text(value, size=size, weight=ft.FontWeight.BOLD, head=True)

    # --- ozdoby grafického návrhu ---------------------------------------------
    def grad(self, top: str, bottom: str) -> ft.LinearGradient:
        return ft.LinearGradient(begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER, colors=[top, bottom])

    def glow(self, strength: float = 14) -> list[ft.BoxShadow]:
        return [ft.BoxShadow(blur_radius=strength, spread_radius=0, color=self.l.glow)]

    def framed(self, content: ft.Control, padding=None, glow: bool = False, bg: str | None = None,
               on_click=None, border_color: str | None = None, corners: bool = True, expand=None) -> ft.Control:
        """Kovový rámeček s vnitřní linkou a zlatými kosočtverci v rozích."""
        pad = padding if isinstance(padding, ft.Padding) else ft.Padding.all(14 if padding is None else padding)
        box = ft.Container(
            content=ft.Container(content=content, padding=pad, border=ft.Border.all(1, self.l.border),
                                 border_radius=ft.BorderRadius.all(max(0, self.l.radius - 2))),
            padding=ft.Padding.all(2), bgcolor=bg or self.l.card,
            border=ft.Border.all(1, border_color or self.l.frame), border_radius=ft.BorderRadius.all(self.l.radius),
            shadow=self.glow() if glow else None, on_click=on_click, ink=on_click is not None,
        )
        if not corners:
            box.expand = expand
            return box
        dots = [ft.Container(width=7, height=7, bgcolor=self.l.orn, rotate=ft.Rotate(0.785), **pos)
                for pos in ({"left": -3, "top": -3}, {"right": -3, "top": -3},
                            {"left": -3, "bottom": -3}, {"right": -3, "bottom": -3})]
        return ft.Stack([box, *dots], clip_behavior=ft.ClipBehavior.NONE, expand=expand, fit=ft.StackFit.PASS_THROUGH)

    def parch(self, content: ft.Control, padding: int = 14) -> ft.Control:
        """Pergamenový (DrD) / ledový (DH) panel pro údaje, které mají vyniknout."""
        return ft.Container(
            content=content, padding=ft.Padding.all(padding), bgcolor=self.l.parch,
            border=ft.Border.all(1, self.l.frame), border_radius=ft.BorderRadius.all(self.l.radius),
            shadow=[ft.BoxShadow(blur_radius=0, spread_radius=3, color=self.l.bg),
                    ft.BoxShadow(blur_radius=0, spread_radius=4, color=self.l.border)],
            margin=ft.Margin.symmetric(horizontal=4, vertical=4),
        )

    def divider(self) -> ft.Control:
        def line(flip: bool) -> ft.Control:
            return ft.Container(height=1, expand=True, gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                colors=["#00000000", self.l.frame] if flip else [self.l.frame, "#00000000"]))
        return ft.Row([line(True), ft.Icon(getattr(ft.Icons, self.l.rune), size=14, color=self.l.orn), line(False)],
                      spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def section(self, value, trailing: ft.Control | None = None, icon=None) -> ft.Control:
        parts: list[ft.Control] = []
        if icon is not None:
            parts.append(ft.Icon(icon, size=20, color=self.l.orn))
        parts.append(self.text(value, size=18, weight=ft.FontWeight.BOLD, head=True))
        parts.append(ft.Container(height=1, expand=True, margin=ft.Margin.symmetric(horizontal=6),
                                  gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT,
                                                             end=ft.Alignment.CENTER_RIGHT,
                                                             colors=[self.l.frame, "#00000000"])))
        if trailing is not None:
            parts.append(trailing)
        return ft.Container(ft.Row(parts, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            margin=ft.Margin.only(top=6))

    # --- kontejnery ----------------------------------------------------------
    def card(self, content: ft.Control, padding: int = 14, accent: bool = False, on_click=None, bg=None) -> ft.Control:
        return self.framed(content, padding=padding, glow=accent, bg=bg, on_click=on_click,
                           border_color=self.l.orn if accent else None)

    def list_card(self, rows: list[ft.Control]) -> ft.Control:
        children: list[ft.Control] = []
        for i, r in enumerate(rows):
            children.append(ft.Container(
                content=r, padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                border=ft.Border.only(bottom=ft.BorderSide(1, self.l.border)) if i < len(rows) - 1 else None,
            ))
        return self.framed(ft.Column(children, spacing=0), padding=0)

    def row_item(self, left: str, right: str = "", sub: str | None = None, on_click=None, badge: str | None = None,
                 trailing: ft.Control | None = None, note: str | None = None) -> ft.Control:
        left_col: list[ft.Control] = []
        title_row: list[ft.Control] = [self.text(left, size=16, weight=ft.FontWeight.BOLD, max_lines=1)]
        if badge:
            title_row.append(self.badge(badge))
        left_col.append(ft.Row(title_row, spacing=8, tight=True))
        if sub:
            left_col.append(self.muted(sub, max_lines=2))
        if note:  # vlastní popis (kurzívou, jeden řádek)
            left_col.append(ft.Text(note, size=13, italic=True, color=self.l.ink, opacity=0.8, max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS))
        controls: list[ft.Control] = [ft.Column(left_col, spacing=2, expand=True)]
        if right:
            short = len(str(right)) <= 7
            controls.append(self.text(right, size=16 if short else 14, weight=ft.FontWeight.BOLD, head=short,
                                      color=None if short else self.l.muted))
        if trailing:
            controls.append(trailing)
        return ft.Container(
            content=ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            on_click=on_click, ink=on_click is not None,
        )

    def badge(self, label: str, color: str | None = None, fg: str | None = None) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=10, weight=ft.FontWeight.BOLD, color=fg or self.l.orn),
            bgcolor=color, border=ft.Border.all(1, self.l.frame), padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=ft.BorderRadius.all(4),
        )

    # --- tlačítka -----------------------------------------------------------
    def button(self, label: str, on_click, primary: bool = True, expand=None, height: int = 48, icon=None,
               disabled: bool = False) -> ft.Control:
        size = 14 if expand else 15
        fg = self.l.on_accent if primary else self.l.ink
        parts: list[ft.Control] = []
        if icon is not None:
            parts.append(ft.Icon(icon, size=18, color=fg if primary else self.l.orn))
        parts.append(ft.Text(label, weight=ft.FontWeight.BOLD, size=size, no_wrap=True, color=fg,
                             font_family=self.hf))
        if primary:
            deco = dict(gradient=self.grad(self.l.accent2, self.l.accent), border=ft.Border.all(1, self.l.orn),
                        shadow=self.glow(12))
        else:
            deco = dict(gradient=self.grad(self.l.card2, self.l.card), border=ft.Border.all(1, self.l.frame))
        return ft.Container(
            content=ft.Row(parts, spacing=8, alignment=ft.MainAxisAlignment.CENTER, tight=True,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            height=height, expand=expand, padding=ft.Padding.symmetric(horizontal=14),
            border_radius=ft.BorderRadius.all(self.l.radius), alignment=ft.Alignment.CENTER,
            on_click=None if disabled else on_click, ink=not disabled, opacity=0.45 if disabled else 1.0,
            disabled=disabled, data="primary" if primary else "secondary", **deco,
        )

    def pill(self, label: str, selected: bool, on_click, expand=None) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=13 if expand else 14, weight=ft.FontWeight.BOLD, no_wrap=True,
                            color=self.l.on_accent if selected else self.l.ink, text_align=ft.TextAlign.CENTER),
            gradient=self.grad(self.l.accent2, self.l.accent) if selected else None,
            bgcolor=None if selected else self.l.card,
            border=ft.Border.all(1, self.l.orn if selected else self.l.border),
            shadow=self.glow(10) if selected else None,
            border_radius=ft.BorderRadius.all(self.l.radius),
            padding=ft.Padding.symmetric(horizontal=6 if expand else 14, vertical=10), on_click=on_click, ink=True,
            alignment=ft.Alignment.CENTER if expand else None, expand=expand,
        )

    def pills(self, options: list[str], selected: str, on_pick: Callable[[str], None], wrap: bool = True,
              equal: bool = False) -> ft.Control:
        items = [self.pill(o, o == selected, lambda e, o=o: on_pick(o), expand=1 if equal else None) for o in options]
        return ft.Row(items, wrap=wrap and not equal, spacing=6, run_spacing=6)

    def search(self, value: str, on_search: Callable[[str], None], hint: str = "Hledat…") -> ft.Control:
        """Vyhledávací pole – hledá po Enteru nebo lupě (překreslení při psaní by bralo fokus)."""
        field = ft.TextField(
            value=value or "", hint_text=hint, dense=True, expand=True, border_color=self.l.frame,
            focused_border_color=self.l.orn, color=self.l.ink, cursor_color=self.l.orn,
            filled=True, fill_color=self.l.bg, border_radius=self.l.radius,
            prefix_icon=ft.Icons.SEARCH, on_submit=lambda e: on_search((field.value or "").strip()),
        )
        row: list[ft.Control] = [field, self.square_button(ft.Icons.ARROW_FORWARD, lambda e: on_search(
            (field.value or "").strip()), "Hledat")]
        if value:
            row.append(self.square_button(ft.Icons.CLOSE, lambda e: on_search(""), "Zrušit hledání"))
        return ft.Row(row, spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def icon_button(self, icon, on_click, tooltip: str, color: str | None = None) -> ft.IconButton:
        return ft.IconButton(icon=icon, on_click=on_click, tooltip=tooltip, icon_color=color or self.l.ink)

    def square_button(self, icon, on_click, tooltip: str) -> ft.IconButton:
        return ft.IconButton(
            icon=icon, on_click=on_click, tooltip=tooltip, icon_color=self.l.orn,
            style=ft.ButtonStyle(bgcolor=self.l.card2, side=ft.BorderSide(1, self.l.frame),
                                 shape=ft.RoundedRectangleBorder(radius=self.l.radius)),
        )

    def stepper(self, value, on_minus, on_plus, label: str | None = None, sub: str | None = None,
                value_color: str | None = None) -> ft.Control:
        core = ft.Row([
            self.square_button(ft.Icons.REMOVE, on_minus, "Snížit"),
            ft.Container(self.text(value, size=21, weight=ft.FontWeight.BOLD, head=True, color=value_color,
                                   align=ft.TextAlign.CENTER), width=max(56, 14 * len(str(value)) + 8),
                         alignment=ft.Alignment.CENTER),
            self.square_button(ft.Icons.ADD, on_plus, "Zvýšit"),
        ], spacing=4, tight=True)
        if label is None:
            return core
        left = [self.text(label, size=16, weight=ft.FontWeight.BOLD)]
        if sub:
            left.append(self.muted(sub))
        return ft.Row([ft.Column(left, spacing=2, expand=True), core],
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # --- čísla ---------------------------------------------------------------
    def stat(self, label: str, value, sub: str | None = None, sub_color: str | None = None, on_click=None) -> ft.Container:
        col = [self.muted(label, size=12, weight=ft.FontWeight.BOLD),
               self.text(value, size=24, weight=ft.FontWeight.BOLD, head=True)]
        if sub is not None:
            col.append(self.text(sub, size=13, weight=ft.FontWeight.BOLD, color=sub_color or self.l.muted))
        return ft.Container(
            content=ft.Container(ft.Column(col, spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                 border=ft.Border.all(1, self.l.border),
                                 border_radius=ft.BorderRadius.all(max(0, self.l.radius - 2)),
                                 padding=ft.Padding.symmetric(vertical=8, horizontal=2),
                                 alignment=ft.Alignment.CENTER),
            gradient=self.grad(self.l.card2, self.l.card), border=ft.Border.all(1, self.l.frame),
            border_radius=ft.BorderRadius.all(self.l.radius), padding=ft.Padding.all(2),
            expand=1, on_click=on_click, ink=on_click is not None,
        )

    def bar(self, value: float, maximum: float, color: str, dark: str | None = None, height: int = 16) -> ft.Control:
        frac = 0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
        full = int(round(frac * 1000))
        parts: list[ft.Control] = []
        if full > 0:
            parts.append(ft.Container(expand=full, border_radius=ft.BorderRadius.all(2),
                                      gradient=self.grad(color, dark or color),
                                      shadow=[ft.BoxShadow(blur_radius=8, color=color + "99")]))
        if full < 1000:
            parts.append(ft.Container(expand=1000 - full))
        return ft.Container(
            content=ft.Row(parts, spacing=0), height=height, padding=ft.Padding.all(2), bgcolor=self.l.bg,
            border=ft.Border.all(1, self.l.frame), border_radius=ft.BorderRadius.all(3),
        )

    def gauge(self, label: str, value, maximum, color: str, extra: str = "", icon=None) -> ft.Control:
        dark = None
        if color == self.l.hp:
            dark, icon = self.l.hp_dark, icon or ft.Icons.FAVORITE
        elif color == self.l.mana:
            dark, icon = self.l.mana_dark, icon or ft.Icons.AUTO_AWESOME
        head: list[ft.Control] = []
        if icon is not None:
            head.append(ft.Icon(icon, size=20, color=color))
        head += [self.text(label, size=17, weight=ft.FontWeight.BOLD, head=True, expand=True),
                 self.text(f"{value} / {maximum}{extra}", size=17, weight=ft.FontWeight.BOLD, head=True)]
        return ft.Column([
            ft.Row(head, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            self.bar(float(value), float(maximum), color, dark),
        ], spacing=6)

    # --- prvky Stolu PJ a propojení (grafický návrh 22. 11.) -------------------
    def avatar(self, initials: str, size: int = 44) -> ft.Control:
        """Kulatý odznak s iniciálami (hráči na Stole PJ)."""
        return ft.Container(
            self.text(initials, size=round(size * .36), weight=ft.FontWeight.BOLD, head=True), width=size,
            height=size, alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(size),
            gradient=ft.RadialGradient(colors=[self.l.card2, self.l.bg], center=ft.Alignment(0, -0.2)),
            border=ft.Border.all(3 if size >= 50 else 2, self.l.orn),
            shadow=[ft.BoxShadow(blur_radius=0, spread_radius=2, color=self.l.bg),
                    ft.BoxShadow(blur_radius=14, color=self.l.glow)],
        )

    def pj_badge(self) -> ft.Control:
        return ft.Container(ft.Text("PJ", size=11, weight=ft.FontWeight.BOLD, color="#ffffff"),
                            bgcolor=self.l.accent, border=ft.Border.all(1, self.l.orn),
                            border_radius=ft.BorderRadius.all(4), padding=ft.Padding.symmetric(horizontal=8, vertical=3))

    def note(self, text: str, icon=ft.Icons.LOCK_OUTLINE) -> ft.Control:
        """Poznámka v rámečku (kdo co vidí, tipy)."""
        return ft.Container(
            ft.Row([ft.Icon(icon, size=18, color=self.l.orn), self.muted(text, size=13, expand=True)], spacing=10,
                   vertical_alignment=ft.CrossAxisAlignment.START),
            padding=ft.Padding.symmetric(horizontal=12, vertical=10), bgcolor=self.l.bg,
            border=ft.Border.all(1, self.l.frame), border_radius=ft.BorderRadius.all(self.l.radius))

    def link(self, label: str, on_click) -> ft.Control:
        """Odkaz v nadpisu oddílu („Vše ›“, „Přidat ›“)."""
        return ft.Container(ft.Row([self.text(label, size=14, weight=ft.FontWeight.BOLD, head=True, color=self.l.orn),
                                    ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=self.l.orn)], spacing=2, tight=True),
                            on_click=on_click, ink=True, padding=ft.Padding.symmetric(vertical=10, horizontal=4))

    def switch_row(self, label: str, value: bool, on_change, icon=None) -> ft.Control:
        parts: list[ft.Control] = []
        if icon is not None:
            parts.append(ft.Icon(icon, size=18, color=self.l.orn))
        parts += [self.text(label, size=15, expand=True),
                  ft.Switch(value=bool(value), on_change=on_change, active_color=self.l.hi)]
        return ft.Row(parts, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def numbered(self, items: list[str]) -> ft.Control:
        rows = []
        for i, t in enumerate(items):
            rows.append(ft.Row([
                ft.Container(self.text(str(i + 1), size=13, weight=ft.FontWeight.BOLD, head=True), width=26, height=26,
                             alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(13), bgcolor=self.l.card2,
                             border=ft.Border.all(1, self.l.orn)),
                ft.Text(spans=_bold_spans(t, self.l.ink), size=15, expand=True, color=self.l.ink),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START))
        return ft.Column(rows, spacing=14)

    def steps_bar(self, cur: int, total: int = 4) -> ft.Control:
        bars = [ft.Container(height=6, expand=1, border_radius=ft.BorderRadius.all(3),
                             bgcolor=self.l.accent2 if i <= cur else self.l.card2,
                             shadow=self.glow(8) if i == cur else None) for i in range(1, total + 1)]
        return ft.Column([self.muted(f"KROK {cur} Z {total}", size=12, weight=ft.FontWeight.BOLD),
                          ft.Row(bars, spacing=6)], spacing=6)

    def check(self, text: str, ok: bool = True, sub: str | None = None, bad: bool = False) -> ft.Control:
        col = self.l.bad if bad else (self.l.ok if ok else self.l.muted)
        icon = ft.Icons.CLOSE if bad else (ft.Icons.CHECK if ok else ft.Icons.CIRCLE_OUTLINED)
        body: list[ft.Control] = [self.text(text, size=15, weight=ft.FontWeight.BOLD)]
        if sub:
            body.append(self.muted(sub, size=13))
        return ft.Row([ft.Icon(icon, size=20, color=col), ft.Column(body, spacing=1, expand=True)], spacing=10,
                      vertical_alignment=ft.CrossAxisAlignment.START)

    def field(self, label: str, value: str = "", mono: bool = False, multiline: bool = False,
              password: bool = False) -> ft.TextField:
        return ft.TextField(label=label, value=value, multiline=multiline, min_lines=3 if multiline else None,
                            max_lines=6 if multiline else 1, border_color=self.l.frame, focused_border_color=self.l.orn,
                            color=self.l.ink, cursor_color=self.l.orn, filled=True, fill_color=self.l.bg,
                            text_size=14 if mono else 16, password=password, can_reveal_password=password,
                            border_radius=self.l.radius)

    def empty(self, text: str) -> ft.Control:
        return ft.Container(self.muted(text, size=14, align=ft.TextAlign.CENTER), padding=ft.Padding.all(20),
                            alignment=ft.Alignment.CENTER)


def column(controls: list[ft.Control], spacing: int = 12, scroll: bool = True, padding: int = 16) -> ft.Control:
    return ft.Container(
        content=ft.Column(controls, spacing=spacing, scroll=ft.ScrollMode.AUTO if scroll else None, expand=True,
                          horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        padding=ft.Padding.only(left=padding, right=padding, top=12, bottom=12), expand=True,
    )


Handler = Optional[Callable]


def fold(s: str) -> str:
    """Malá písmena bez diakritiky – pro hledání."""
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(ch) != "Mn")


def matches(query: str, *texts) -> bool:
    if not query:
        return True
    hay = fold(" ".join(str(t) for t in texts if t))
    return all(w in hay for w in fold(query).split())


def _bold_spans(text: str, color: str) -> list[ft.TextSpan]:
    """„Klikni na <b>Run</b>“ → úseky s tučným písmem."""
    out: list[ft.TextSpan] = []
    for i, part in enumerate(str(text).replace("</b>", "<b>").split("<b>")):
        if part:
            out.append(ft.TextSpan(part, style=ft.TextStyle(weight=ft.FontWeight.BOLD if i % 2 else None,
                                                             color=color)))
    return out
