"""Rozcestník obrazovek."""
from __future__ import annotations

from . import catalog, character, dice, druzina, inventory, journal, magic, pj, propojeni, start

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
    "pj_kampan": pj.pj_kampan,
    "pj_souboj": pj.pj_souboj,
    "pj_bestiar": pj.pj_bestiar,
    "pj_nastroje": pj.pj_nastroje,
    "pj_poznamky": pj.pj_poznamky,
    "propojeni": propojeni.propojeni,
    "pruvodce": propojeni.pruvodce,
    "pj_login": propojeni.pj_login,
}
PJ = ("pj_kampan", "pj_souboj", "pj_bestiar", "pj_nastroje", "pj_poznamky")
FREE = ("start", "generator", "propojeni", "pruvodce", "pj_login")


def build(app):
    if app.screen in PJ and app.camp is None:
        app.screen = "start"
    elif app.screen not in FREE and app.screen not in PJ and app.char is None:
        app.screen = "start"
    return BUILDERS[app.screen](app)
