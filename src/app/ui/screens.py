"""Rozcestník obrazovek."""
from __future__ import annotations

from . import catalog, character, dice, druzina, inventory, journal, magic, start

BUILDERS = {
    "start": start.start,
    "generator": start.generator,
    "postava": character.postava,
    "postup": character.postup,
    "dovednosti": character.dovednosti,
    "batoh": inventory.batoh,
    "kostky": dice.kostky,
    "souboj": dice.souboj,
    "bestiar": journal.bestiar,
    "denik": journal.denik,
    "kouzla": magic.kouzla,
    "obor": magic.obor,
    "alchymie": magic.alchymie,
    "druzina": druzina.druzina,
    "katalog": catalog.katalog,
}


def build(app):
    if app.screen not in ("start", "generator") and app.char is None:
        app.screen = "start"
    return BUILDERS[app.screen](app)
