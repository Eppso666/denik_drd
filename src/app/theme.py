"""Dva oddělené vzhledy: Dračí Hlídka (tmavý, oranžový) a Dračí doupě 1.6 (pergamen, vínová)."""
from __future__ import annotations

from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class Look:
    key: str
    dark: bool
    bg: str
    card: str
    card2: str
    border: str
    ink: str
    muted: str
    accent: str
    on_accent: str
    hp: str
    mana: str
    ok: str
    warn: str
    bad: str
    head_font: str | None
    body_font: str | None
    radius: int
    nav_bg: str


START = Look("start", True, "#121015", "#1c1920", "#2a2630", "#36313d", "#f2ede4", "#b4aca0", "#d4b25c", "#141217",
             "#d9574a", "#8cc0f0", "#8fd19e", "#e8944a", "#d9574a", "Cinzel", None, 14, "#1c1920")
DH = Look("dh", True, "#141217", "#1f1c23", "#2a2630", "#3a3541", "#f2ede4", "#b4aca0", "#e8944a", "#141217",
          "#d9574a", "#8cc0f0", "#8fd19e", "#e8944a", "#d9574a", "Cinzel", None, 14, "#1f1c23")
DRD = Look("drd", False, "#f1e6cf", "#fbf5e6", "#efe2c6", "#c9b48a", "#2b1d12", "#5e4a33", "#8a2b1e", "#fbf5e6",
           "#8a2b1e", "#2f5d8a", "#2f6b3a", "#8a6414", "#8a2b1e", "IMFell", "Alegreya", 6, "#e6d6b3")


def for_system(system: str | None) -> Look:
    if system == "dh":
        return DH
    if system == "drd":
        return DRD
    return START


def apply(page: ft.Page, look: Look, fonts_available: set[str]) -> None:
    body = look.body_font if look.body_font in fonts_available else None
    scheme = ft.ColorScheme(
        primary=look.accent,
        on_primary=look.on_accent,
        secondary=look.accent,
        on_secondary=look.on_accent,
        surface=look.card,
        on_surface=look.ink,
        on_surface_variant=look.muted,
        outline=look.border,
        outline_variant=look.border,
        error=look.bad,
    )
    page.theme = ft.Theme(color_scheme=scheme, font_family=body, use_material3=True)
    page.dark_theme = page.theme
    page.theme_mode = ft.ThemeMode.DARK if look.dark else ft.ThemeMode.LIGHT
    page.bgcolor = look.bg


def head(look: Look, fonts_available: set[str]) -> str | None:
    return look.head_font if look.head_font in fonts_available else None
