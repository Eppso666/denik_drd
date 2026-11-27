"""Rozcestník obrazovek."""
from __future__ import annotations

from . import catalog, character, dice, druzina, inventory, journal, magic, pj, start

BUILDERS = {
    "uvod": start.uvod,
    "start": start.start,
    "doupe": start.doupe,
    "generator": start.generator,
    "postava": character.postava,
    "postup": character.postup,
    "dovednosti": character.dovednosti,
    "batoh": inventory.batoh,
    "kostky": dice.kostky,
    "denik": journal.denik,
    "kouzla": magic.kouzla,
    "obor": magic.obor,
    "alchymie": magic.alchymie,
    "druzina": druzina.druzina,
    "katalog": catalog.katalog,
    "pj_kampan": pj.pj_kampan,
    "pj_souboj": pj.pj_souboj,
    "pj_bestiar": pj.pj_bestiar,
    "pj_nastroje": pj.pj_nastroje,
    "pj_poznamky": pj.pj_poznamky,
}


def build(app):
    if app.screen not in BUILDERS:  # např. Bestiář hráče už není – zůstal jen Pánovi jeskyně
        app.screen = "postava" if app.char else "start"
    if app.screen.startswith("pj_"):
        # Stůl PJ jen pro otevřenou kampaň, jejíž heslo bylo v tomto spuštění zadáno
        if app.camp is None or app.gm_active not in app.gm_unlocked:
            app.gm_active = None
            app.screen = "doupe"
    elif app.screen not in ("uvod", "start", "doupe", "generator") and app.char is None:
        app.screen = "start"
    return BUILDERS[app.screen](app)
