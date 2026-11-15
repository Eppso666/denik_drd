"""Kouřový test UI: sestaví každou obrazovku obou her a „klikne“ na všechna tlačítka a dialogy."""
import flet as ft
import pytest

from app import model
from app.ui import start
from conftest import Ev, drain, walk

SCREENS = ["postava", "batoh", "katalog", "kostky", "souboj", "postup", "dovednosti", "bestiar", "denik"]


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
                                        ("drd", "Hraničář"), ("drd", "Kouzelník")])
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


def _drd_char(app, page, cls, level=1, branch=None, attrs=(10, 12, 12, 17, 14), race="Člověk"):
    c = model.create_character("drd", "Test", race, cls, list(attrs))
    c["level"] = level
    c["branch"] = branch
    app.add_character(c)
    app.open_character(c["id"])
    drain(page)
    return c


def test_wizard_spells_and_familiar(make_app):
    from app.rules import drd_kouzla
    from app.ui import companions, magic
    app, page = make_app()
    c = _drd_char(app, page, "Kouzelník")
    assert c["mana_max"] == 8  # INT 17, 1. úroveň
    app.go("kouzla")
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Dým" in texts and "Ohnivý déšť" in texts and "Bábelská rybka" not in texts  # PPP až od 6. úr.
    # naučit se 3 kouzla (limit 1. úrovně), čtvrté už ne
    for name in ("Modré blesky", "Dým", "Hyperprostor", "Světlo"):
        names = c["spells"]
        if len(names) < 3:
            names.append(name)
    assert len(c["spells"]) == magic.spell_limit(c) == 3
    app.go("postava")
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert any("Kouzla 3/3" in str(t) for t in texts)
    magic.spell_detail(app, c, drd_kouzla.SPELL_BY_NAME["Modré blesky"], known=True)
    assert page.dialogs
    page.dialogs.clear()
    companions.add_companion(app, c, "přítel", "Havran")
    drain(page)
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Havran" in texts and "ÚČ" in texts
    # čaroděj na 11. úrovni má silnějšího havrana
    c["level"], c["branch"] = 11, "Čaroděj"
    from app.rules import drd_obory
    st = drd_obory.companion_stats(c["companions"][0], c["cls"], c["level"], c["branch"])
    assert st["Magenergie"] == "15" and st["Počet kouzel"] == "6"
    app.go("kouzla")
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Bábelská rybka" in texts
    for scr in ("kouzla", "obor", "postava", "postup"):
        app.go(scr)
        assert click_everything(app, page) > 0, scr


def test_postup_to_6_requires_branch(make_app):
    from app.ui import character
    app, page = make_app()
    c = _drd_char(app, page, "Zloděj", level=5, attrs=(10, 16, 12, 10, 14))
    character.open_postup(app)
    assert app.ui["lvl"]["level"] == 6
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Lupič" in texts and "Sicco" in texts
    save_btn = [x for v in page.views for x in walk(v) if isinstance(x, ft.FilledButton)][-1]
    save_btn.on_click(Ev(save_btn))
    drain(page)
    assert c["level"] == 5 and not c.get("branch")  # bez volby oboru se neuloží
    app.ui["lvl"]["branch"] = "Lupič"
    app.go("postup")
    save_btn = [x for v in page.views for x in walk(v) if isinstance(x, ft.FilledButton)][-1]
    save_btn.on_click(Ev(save_btn))
    drain(page)
    assert c["level"] == 6 and c["branch"] == "Lupič"
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Nenápadnost" in texts and "Křišťálový klíč" in texts


def test_ranger_dog(make_app):
    from app.ui import companions
    app, page = make_app()
    c = _drd_char(app, page, "Hraničář", level=1)
    companions.add_companion(app, c, "pes", "Pes válečný")
    drain(page)
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "Pes válečný" in texts
    c["level"] = 6  # pes je u pána 5 úrovní → zesílí
    app.go("postava")
    texts = [getattr(x, "value", "") for v in page.views for x in walk(v)]
    assert "ZESÍLIL" in texts and "6" in texts


def test_catalog_add_and_buy(make_app):
    from app.ui import catalog
    app, page = make_app()
    c = _drd_char(app, page, "Válečník", attrs=(16, 12, 15, 10, 10))
    c["money"] = {"zl": 30, "st": 0, "md": 0}
    items = catalog.rules_catalog(c)
    sword = next(i for i in items if i["name"] == "Široký meč")
    assert (sword["attack"], sword["damage"], sword["defense"], sword["weight_mn"]) == (5, 0, 0, 30)
    catalog.item_dialog(app, sword)
    buy = next(a for a in page.dialogs[-1].actions if a.content == "Koupit")
    buy.on_click(Ev(buy))
    drain(page)
    assert c["money"] == {"zl": 6, "st": 0, "md": 0}
    assert any(i["name"] == "Široký meč" and i["equipped"] for i in c["items"])
    assert model.weapons(c)[0]["attack"] == 5
    # bez zbroje má DrD postava KZ 1; s kroužkovou 5
    assert model.armor_quality(c) == 1
    mail = next(i for i in items if i["name"] == "Kroužková zbroj")
    assert mail["weight_mn"] == 350 and mail["quality"] == 5
    assert catalog.price_md("1 zl 5 st") == 150
