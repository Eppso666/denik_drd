"""Vzhledy podle schváleného grafického návrhu:
Dračí doupě 1.6 – Fire Fantasy (tmavý kámen, bronz, zlato, rudá záře, pergamen),
Dračí Hlídka – Ice Fantasy (temně modrá, stříbro, ledová záře, ledový kámen),
úvod – společný tmavý vzhled se zlatem."""
from __future__ import annotations

from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class Look:
    key: str
    dark: bool
    bg: str          # pozadí
    card: str        # karta
    card2: str       # vyvýšená karta, tlačítka
    border: str      # vnitřní linky, oddělovače
    ink: str         # text
    muted: str       # tlumený text
    accent: str      # akcent (tmavší konec přechodu)
    on_accent: str   # text na akcentu
    hp: str          # životy (jasný konec)
    mana: str        # mana / magenergie (jasný konec)
    ok: str
    warn: str
    bad: str
    head_font: str | None
    body_font: str | None
    radius: int
    nav_bg: str      # horní a spodní lišta
    # --- prvky grafického návrhu ---
    bg2: str = "#1b1820"      # horní konec přechodu pozadí a lišt
    frame: str = "#b79a5a"    # kovový rámeček
    orn: str = "#d4b25c"      # ornamenty, ikony, odkazy
    accent2: str = "#d4b25c"  # světlý konec přechodu akcentu
    glow: str = "#59d4b25c"   # záře (ARGB)
    parch: str = "#ece3d0"    # pergamen / ledový kámen
    ptext: str = "#221a10"    # text na pergamenu
    pmuted: str = "#5a4a33"
    pwarn: str = "#7a4a00"
    pbad: str = "#8f1d12"
    hp_dark: str = "#7d1410"
    mana_dark: str = "#1f4f8c"
    banner: str | None = None  # ilustrace v záhlaví postavy
    rune: str = "AUTO_AWESOME"  # ikona v oddělovačích


START = Look("start", True, "#121015", "#211d26", "#2c2733", "#3a3442", "#f2ede4", "#bdb4a6", "#8f6d24", "#1a1408",
             "#d8352a", "#4f95e0", "#8fd19e", "#e8ad5a", "#f07a68", "Cinzel", "Alegreya", 6, "#1b1820",
             bg2="#1b1820", frame="#b79a5a", orn="#d4b25c", accent2="#d4b25c", glow="#59d4b25c",
             parch="#ece3d0", ptext="#221a10", pmuted="#5a4a33")
DRD = Look("drd", True, "#140d0a", "#251912", "#33231a", "#4a3322", "#f4e7cf", "#c9b28f", "#a8281f", "#fff1dc",
           "#d8352a", "#4f95e0", "#86c98f", "#e9ad52", "#f07a68", "Cinzel", "Alegreya", 6, "#1d1310",
           bg2="#1d1310", frame="#a8793f", orn="#d9a94e", accent2="#d8452f", glow="#73d8452f",
           parch="#e9d7b1", ptext="#2a1c10", pmuted="#5a4329", pwarn="#7a4a00", pbad="#8f1d12",
           hp_dark="#7d1410", mana_dark="#1f4f8c", banner="img/drd_banner.jpg", rune="LOCAL_FIRE_DEPARTMENT_OUTLINED")
DH = Look("dh", True, "#0b1f3b", "#1d3150", "#2a3646", "#33476a", "#f0f6ff", "#b4c3d8", "#1f8fc4", "#04192e",
          "#4fc3f7", "#a493ff", "#8fe0b0", "#ffc46b", "#ff8a8a", "Cinzel", "Alegreya", 6, "#142b48",
          bg2="#142b48", frame="#c0c6d4", orn="#c0c6d4", accent2="#4fc3f7", glow="#804fc3f7",
          parch="#dfe8f3", ptext="#0f2238", pmuted="#3b5371", pwarn="#7a4a00", pbad="#9a1f2a",
          hp_dark="#1a6aa8", mana_dark="#4a3aa8", banner="img/dh_banner.jpg", rune="AC_UNIT")


def _hi(self: Look) -> str:
    """Čitelná zvýrazňující barva textu a ikon na tmavém pozadí."""
    return self.accent2 if self.key == "dh" else self.orn


Look.hi = property(_hi)


def for_system(system: str | None) -> Look:
    if system == "dh":
        return DH
    if system == "drd":
        return DRD
    return START


def apply(page: ft.Page, look: Look, fonts_available: set[str]) -> None:
    body = look.body_font if look.body_font in fonts_available else None
    head_font = look.head_font if look.head_font in fonts_available else None
    scheme = ft.ColorScheme(
        primary=look.accent2,
        on_primary=look.on_accent,
        secondary=look.orn,
        on_secondary=look.bg,
        surface=look.card,
        on_surface=look.ink,
        on_surface_variant=look.muted,
        outline=look.frame,
        outline_variant=look.border,
        error=look.bad,
    )
    shape = ft.RoundedRectangleBorder(radius=look.radius + 2, side=ft.BorderSide(1, look.frame))
    page.theme = ft.Theme(
        color_scheme=scheme, font_family=body, use_material3=True,
        dialog_theme=ft.DialogTheme(bgcolor=look.card, shape=shape, barrier_color="#b3000000"),
        text_button_theme=ft.TextButtonTheme(style=ft.ButtonStyle(
            color=look.orn, text_style=ft.TextStyle(font_family=head_font, weight=ft.FontWeight.BOLD, size=14))),
        floating_action_button_theme=ft.FloatingActionButtonTheme(
            bgcolor=look.accent, foreground_color=look.on_accent,
            shape=ft.CircleBorder()),
        divider_color=look.border,
    )
    page.dark_theme = page.theme
    page.theme_mode = ft.ThemeMode.DARK if look.dark else ft.ThemeMode.LIGHT
    page.bgcolor = look.bg


def head(look: Look, fonts_available: set[str]) -> str | None:
    return look.head_font if look.head_font in fonts_available else None
