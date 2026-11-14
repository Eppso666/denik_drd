"""Kouřový test UI: sestaví každou obrazovku obou her a „klikne“ na všechna tlačítka a dialogy."""
import flet as ft
import pytest

from app import model
from app.ui import start
from conftest import Ev, drain, walk

SCREENS = ["postava", "batoh", "kostky", "souboj", "postup", "dovednosti", "bestiar", "denik"]


def handlers(view_list):
    for v in view_list:
        for c in walk(v):
            for attr in ("on_click", "on_change"):
                h = getattr(c, attr, None)
                if callable(h):
                    yield c, attr, h


def click_everything(app, page, rounds=2):
    """Klikne na každý ovládací prvek aktuální obrazovky a potvrdí otevřené dialogy."""
    clicked = 0
    for _ in range(rounds):
        snapshot = list(handlers(page.views))
        screen = app.screen
        for ctrl, attr, h in snapshot:
            if attr == "on_change" and isinstance(ctrl, ft.NavigationBar):
                ctrl.selected_index = 0
            h(Ev(ctrl))
            clicked += 1
            # potvrď / zavři dialogy
            while page.dialogs:
                d = page.dialogs[-1]
                acts = getattr(d, "actions", None) or []
                target = None
                for a in reversed(acts):
                    if callable(getattr(a, "on_click", None)):
                        target = a
                        break
                if target is None:
                    page.dialogs.pop()
                    continue
                n = len(page.dialogs)
                target.on_click(Ev(target))
                if len(page.dialogs) >= n:
                    page.dialogs.pop()
            drain(page)
            if app.screen != screen or app.char is None:
                if app.char is None:
                    return clicked
                app.go(screen)
    return clicked


@pytest.mark.parametrize("system", ["dh", "drd"])
def test_all_screens_build_and_click(make_app, system):
    app, page = make_app()
    race = "Trpaslík"
    cls = "Válečník"
    attrs = [18, 9, 19, 10, 7] if system == "dh" else [16, 8, 15, 10, 5]
    c = model.create_character(system, "Test Testovič", race, cls, attrs)
    c["abilities"].append({"name": "Stopování", "pct": 60, "attr": None, "kind": "Schopnost povolání"})
    app.add_character(c)
    app.bestiary[system].append({"id": "b1", "name": "Krysa", "hp": 7, "uc": 2, "oc": 4, "dmg": 1})
    app.open_character(c["id"])
    drain(page)
    for s in SCREENS:
        app.active = c["id"]
        app.go(s)
        assert page.views, s
        n = click_everything(app, page)
        assert n > 0, s
    assert app.store.data, "nic se neuložilo"


def test_generator_both_systems_manual_and_auto(make_app):
    app, page = make_app()
    app.render()
    start.open_generator(app)
    for sys_name in ("Dračí Hlídka", "Dračí doupě 1.6"):
        for mode in ("Automaticky", "Ručně"):
            app.ui["gen_sys"] = "dh" if sys_name == "Dračí Hlídka" else "drd"
            app.ui["gen_mode"] = "auto" if mode == "Automaticky" else "manual"
            start.reset_gen(app)
            app.go("generator")
            # zvýšit první vlastnost a ubrat poslední
            if mode == "Ručně":
                start.step(app, 4, -1)
                start.step(app, 0, +1)
                start.step(app, 1, +1)  # pool je plný → nesmí přidat
                if app.ui["gen_sys"] == "dh":
                    assert sum(app.ui["gen_points"]) == 20
                    assert app.ui["gen_points"] == [5, 4, 4, 4, 3]
    # vytvoř postavu DrD přes tlačítko
    app.ui.update({"gen_sys": "drd", "gen_mode": "auto", "gen_name": "Elwin"})
    start.reset_gen(app)
    app.go("generator")
    buttons = [c for c, a, h in handlers(page.views) if isinstance(c, ft.FilledButton)]
    buttons[-1].on_click(Ev(buttons[-1]))
    drain(page)
    assert app.char and app.char["system"] == "drd" and app.char["name"] == "Elwin"
    assert app.screen == "postava"


def test_start_empty_and_list(make_app):
    app, page = make_app()
    app.render()
    assert page.views
    c = model.create_character("dh", "A", "Elf", "Kouzelník", [10, 10, 10, 10, 10])
    app.add_character(c)
    app.render()
    drain(page)
    assert app.store.data["order"] == [c["id"]]


def test_persistence_roundtrip(make_app):
    app, page = make_app()
    c = model.create_character("drd", "B", "Hobit", "Zloděj", [5, 16, 10, 12, 14])
    app.add_character(c)
    drain(page)
    app2, page2 = make_app()
    app2.store = app.store
    import asyncio
    asyncio.run(app2.load())
    assert app2.chars[c["id"]]["name"] == "B"
