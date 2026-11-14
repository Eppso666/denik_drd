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

    def section(self, value, trailing: ft.Control | None = None) -> ft.Control:
        t = self.text(value.upper() if self.l.key != "drd" else value, size=14 if self.l.key != "drd" else 18,
                      weight=ft.FontWeight.BOLD, color=self.l.accent, head=True)
        if trailing is None:
            return t
        return ft.Row([t, trailing], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # --- kontejnery ----------------------------------------------------------
    def card(self, content: ft.Control, padding: int = 14, accent: bool = False, on_click=None, bg=None) -> ft.Container:
        return ft.Container(
            content=content, padding=ft.Padding.all(padding), bgcolor=bg or self.l.card,
            border=ft.Border.all(2 if accent else 1, self.l.accent if accent else self.l.border),
            border_radius=ft.BorderRadius.all(self.l.radius), on_click=on_click, ink=on_click is not None,
        )

    def list_card(self, rows: list[ft.Control]) -> ft.Container:
        children: list[ft.Control] = []
        for i, r in enumerate(rows):
            children.append(ft.Container(
                content=r, padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                border=ft.Border.only(bottom=ft.BorderSide(1, self.l.card2)) if i < len(rows) - 1 else None,
            ))
        return ft.Container(
            content=ft.Column(children, spacing=0), bgcolor=self.l.card,
            border=ft.Border.all(1, self.l.border), border_radius=ft.BorderRadius.all(self.l.radius),
        )

    def row_item(self, left: str, right: str = "", sub: str | None = None, on_click=None, badge: str | None = None,
                 trailing: ft.Control | None = None) -> ft.Control:
        left_col: list[ft.Control] = []
        title_row: list[ft.Control] = [self.text(left, size=15, weight=ft.FontWeight.W_600, max_lines=1)]
        if badge:
            title_row.append(self.badge(badge))
        left_col.append(ft.Row(title_row, spacing=8, tight=True))
        if sub:
            left_col.append(self.muted(sub, max_lines=2))
        controls: list[ft.Control] = [ft.Column(left_col, spacing=2, expand=True)]
        if right:
            controls.append(self.muted(right, size=14))
        if trailing:
            controls.append(trailing)
        return ft.Container(
            content=ft.Row(controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            on_click=on_click, ink=on_click is not None,
        )

    def badge(self, label: str, color: str | None = None, fg: str | None = None) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=10, weight=ft.FontWeight.BOLD, color=fg or self.l.ink),
            bgcolor=color or self.l.card2, padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            border_radius=ft.BorderRadius.all(4),
        )

    # --- tlačítka -----------------------------------------------------------
    def button(self, label: str, on_click, primary: bool = True, expand=None, height: int = 48, icon=None,
               disabled: bool = False) -> ft.Control:
        size = 14 if expand else None
        if primary:
            return ft.FilledButton(
                content=ft.Text(label, weight=ft.FontWeight.BOLD, size=size, no_wrap=True),
                icon=icon, on_click=on_click, expand=expand,
                height=height, disabled=disabled,
                style=ft.ButtonStyle(bgcolor=self.l.accent, color=self.l.on_accent,
                                     shape=ft.RoundedRectangleBorder(radius=self.l.radius)),
            )
        return ft.OutlinedButton(
            content=ft.Text(label, weight=ft.FontWeight.W_600, size=size, no_wrap=True), icon=icon,
            on_click=on_click, expand=expand,
            height=height, disabled=disabled,
            style=ft.ButtonStyle(color=self.l.ink, side=ft.BorderSide(1, self.l.border),
                                 shape=ft.RoundedRectangleBorder(radius=self.l.radius)),
        )

    def pill(self, label: str, selected: bool, on_click, expand=None) -> ft.Container:
        return ft.Container(
            content=ft.Text(label, size=12 if expand else 13, weight=ft.FontWeight.BOLD, no_wrap=True,
                            color=self.l.on_accent if selected else self.l.ink, text_align=ft.TextAlign.CENTER),
            bgcolor=self.l.accent if selected else self.l.card,
            border=ft.Border.all(1, self.l.accent if selected else self.l.border),
            border_radius=ft.BorderRadius.all(999 if self.l.key != "drd" else 4),
            padding=ft.Padding.symmetric(horizontal=6 if expand else 12, vertical=10), on_click=on_click, ink=True,
            alignment=ft.Alignment.CENTER if expand else None, expand=expand,
        )

    def pills(self, options: list[str], selected: str, on_pick: Callable[[str], None], wrap: bool = True,
              equal: bool = False) -> ft.Control:
        items = [self.pill(o, o == selected, lambda e, o=o: on_pick(o), expand=1 if equal else None) for o in options]
        return ft.Row(items, wrap=wrap and not equal, spacing=6, run_spacing=6)

    def icon_button(self, icon, on_click, tooltip: str, color: str | None = None) -> ft.IconButton:
        return ft.IconButton(icon=icon, on_click=on_click, tooltip=tooltip, icon_color=color or self.l.ink)

    def stepper(self, value, on_minus, on_plus, label: str | None = None, sub: str | None = None,
                value_color: str | None = None) -> ft.Control:
        btn = lambda ic, cb, tip: ft.IconButton(  # noqa: E731
            icon=ic, on_click=cb, tooltip=tip, icon_color=self.l.ink,
            style=ft.ButtonStyle(bgcolor=self.l.card2, shape=ft.RoundedRectangleBorder(radius=self.l.radius)),
        )
        core = ft.Row([
            btn(ft.Icons.REMOVE, on_minus, "Snížit"),
            ft.Container(self.text(value, size=20, weight=ft.FontWeight.BOLD, head=True, color=value_color,
                                   align=ft.TextAlign.CENTER), width=52, alignment=ft.Alignment.CENTER),
            btn(ft.Icons.ADD, on_plus, "Zvýšit"),
        ], spacing=4, tight=True)
        if label is None:
            return core
        left = [self.text(label, size=15, weight=ft.FontWeight.W_600)]
        if sub:
            left.append(self.muted(sub))
        return ft.Row([ft.Column(left, spacing=2, expand=True), core],
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # --- čísla ---------------------------------------------------------------
    def stat(self, label: str, value, sub: str | None = None, sub_color: str | None = None, on_click=None) -> ft.Container:
        col = [self.muted(label, size=11, weight=ft.FontWeight.BOLD),
               self.text(value, size=22, weight=ft.FontWeight.BOLD, head=True)]
        if sub is not None:
            col.append(self.text(sub, size=12, weight=ft.FontWeight.BOLD, color=sub_color or self.l.muted))
        return ft.Container(
            content=ft.Column(col, spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=self.l.card, border=ft.Border.all(1, self.l.border),
            border_radius=ft.BorderRadius.all(self.l.radius), padding=ft.Padding.symmetric(vertical=8, horizontal=2),
            expand=1, on_click=on_click, ink=on_click is not None,
        )

    def bar(self, value: float, maximum: float, color: str) -> ft.ProgressBar:
        frac = 0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
        return ft.ProgressBar(value=frac, color=color, bgcolor=self.l.card2, bar_height=10,
                              border_radius=ft.BorderRadius.all(4))

    def gauge(self, label: str, value, maximum, color: str, extra: str = "") -> ft.Control:
        return ft.Column([
            ft.Row([self.text(label, size=14, weight=ft.FontWeight.W_600),
                    self.text(f"{value} / {maximum}{extra}", size=14)],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.bar(float(value), float(maximum), color),
        ], spacing=5)

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
