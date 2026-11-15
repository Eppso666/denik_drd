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


@pytest.mark.parametrize("system,cls", [("dh", "Válečník"), ("drd", "Válečník"), ("drd", "Zloděj"),
                                        ("drd", "Hraničář")])
def test_all_screens_build_and_click(make_app, system, cls):
    app, page = make_app()
    race = "Trpaslík"
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
    # po vytvoření se aplikace vrátí na seznam postav
    assert app.screen == "start"
    c = app.chars[app.order[0]]
    assert c["system"] == "drd" and c["name"] == "Elwin"


def test_avatar_pick_and_remove(make_app):
    import asyncio
    from app.ui import avatar as avatar_ui
    app, page = make_app()
    c = model.create_character("drd", "Elwin Stříbrný", "Elf", "Kouzelník", [10, 12, 10, 16, 14])
    app.add_character(c)
    app.open_character(c["id"])
    drain(page)

    async def fake_pick():
        return b"\x89PNG fake"
    app.pick_image = fake_pick
    asyncio.run(avatar_ui.pick_avatar(app, c))
    drain(page)
    assert c["avatar"] and app.images[c["avatar"]] == b"\x89PNG fake"
    app.go("postava")
    assert any(isinstance(x, ft.Image) for v in page.views for x in walk(v))
    app.go("start")
    assert any(isinstance(x, ft.Image) for v in page.views for x in walk(v))
    avatar_ui.avatar_menu(app, c)
    assert page.dialogs
    asyncio.run(avatar_ui.remove_avatar(app, c))
    drain(page)
    assert c["avatar"] is None


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


def test_drd_generator_class_card_and_levels(make_app):
    app, page = make_app()
    app.render()
    start.open_generator(app)
    app.ui.update({"gen_sys": "drd", "gen_cls": "Zloděj", "gen_race": "Hobit"})
    start.reset_gen(app)
    app.go("generator")
    texts = [getattr(c, "value", "") for v in page.views for c in walk(v)]
    assert "Převleky" in texts and "ZÁKLADNÍ VLASTNOSTI POVOLÁNÍ" in texts
    pill5 = next(c for v in page.views for c in walk(v)
                 if isinstance(c, ft.Container) and getattr(getattr(c, "content", None), "value", None) == "5")
    pill5.on_click(Ev(pill5))
    drain(page)
    assert app.ui["gen_lvl"] == 5
