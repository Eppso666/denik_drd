"""Deník dobrodruha – mobilní deník postavy pro Dračí Hlídku a Dračí doupě 1.6."""
from __future__ import annotations

import os

import flet as ft

from app.core import App

FONT_FILES = {
    "Cinzel": "fonts/Cinzel.ttf",
    "IMFell": "fonts/IMFellEnglishSC.ttf",
    "Alegreya": "fonts/AlegreyaSans-Regular.ttf",
}


def available_fonts() -> dict[str, str]:
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    return {name: path for name, path in FONT_FILES.items() if os.path.exists(os.path.join(here, path))}


async def main(page: ft.Page) -> None:
    page.title = "Deník dobrodruha"
    fonts = available_fonts()
    if fonts:
        page.fonts = fonts
    app = App(page, set(fonts))
    page.on_view_pop = app.on_view_pop
    await app.load()
    app.take_invite(_invite_from(page))
    app.render()


def _invite_from(page: ft.Page) -> str | None:
    """Webová verze otevřená z QR pozvánky (…/?pozvanka=…)."""
    for getter in (lambda: page.query.get("pozvanka"), lambda: page.route, lambda: getattr(page, "url", None)):
        try:
            val = getter()
        except Exception:
            continue
        if val and "pozvanka=" in str(val):
            return str(val)
        if val and getter is not None and len(str(val)) > 40 and "/" not in str(val):
            return "pozvanka=" + str(val)
    return None


if __name__ == "__main__":
    ft.run(main)
