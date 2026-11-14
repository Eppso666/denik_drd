"""Rozcestník obrazovek."""
from __future__ import annotations

from . import character, dice, inventory, journal, start

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
}


def build(app):
    if app.screen not in ("start", "generator") and app.char is None:
        app.screen = "start"
    return BUILDERS[app.screen](app)
