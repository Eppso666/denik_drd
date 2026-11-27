"""Deník dobrodruha – mobilní deník postavy pro Dračí Hlídku a Dračí doupě 1.6."""
from __future__ import annotations

import os
import sys

import flet as ft

from app.core import App

FONT_FILES = {
    "Cinzel": "fonts/Cinzel.ttf",
    "IMFell": "fonts/IMFellEnglishSC.ttf",
    "Alegreya": "fonts/AlegreyaSans-Regular.ttf",
}


def available_fonts() -> dict[str, str]:
    """Písma ze složky assets. Ve webové verzi (Pyodide) a v telefonu Python složku assets nevidí –
    písma tam ale sestavení přibalí (scripts/fetch_fonts.sh), takže se zapnou vždy."""
    if sys.platform in ("emscripten", "android", "ios") or os.environ.get("FLET_PLATFORM") in ("android", "ios") \
            or hasattr(sys, "getandroidapilevel"):
        return dict(FONT_FILES)
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
    app.render()


if __name__ == "__main__":
    ft.run(main)
