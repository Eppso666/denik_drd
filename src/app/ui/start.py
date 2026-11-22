"""Společné obrazovky: výběr postavy a generátor postavy."""
from __future__ import annotations

import flet as ft

from .. import model, theme, version
from ..version import VERSION
from ..rules import dh, drd
from ..rules.common import fmt
from . import avatar as avatar_ui
from . import backup
from .kit import Kit, column

SYS = {"dh": dh, "drd": drd}


def start(app):
    """Úvod podle grafického návrhu (Tvoje postavy) doplněný o část Vedu hru (Stůl PJ)."""
    from ..core import Screen
    from . import propojeni

    k = app.kit
    l = app.look
    mode = app.ui.get("start_mode", "Hraju")
    controls: list[ft.Control] = [k.text("DENÍK DOBRODRUHA", size=12, weight=ft.FontWeight.BOLD, color=l.orn)]
    seen = app.settings.get("seen_version")
    if seen != VERSION:
        news = version.news_since(seen) if (app.order or app.gm_order) else []
        if not news:
            app.settings["seen_version"] = VERSION
            app.save(settings=True)
        else:
            def ok(e):
                app.settings["seen_version"] = VERSION
                app.save(settings=True)
                app.refresh()
            lines: list[ft.Control] = [k.text(f"Nová verze {VERSION}", size=17, weight=ft.FontWeight.BOLD, head=True)]
            for v, items in news:
                lines += [k.text(f"• {t}", size=13) for t in items]
            lines.append(ft.Row([k.button("Rozumím", ok, primary=False, height=40)], alignment=ft.MainAxisAlignment.END))
            controls.append(k.framed(ft.Column(lines, spacing=6), glow=True))

    def set_mode(v):
        app.ui["start_mode"] = v
        app.refresh()

    controls.append(k.pills(["Hraju", "Vedu hru (PJ)"], mode, set_mode, equal=True))
    if app.ui.get("invite_text"):
        controls.append(k.card(ft.Column([
            k.text("Máš pozvánku do kampaně", size=16, weight=ft.FontWeight.BOLD, head=True),
            k.muted("Otevři postavu, se kterou se připojíš, a klepni na Družina – pozvánka je předvyplněná.", size=13),
        ], spacing=4), accent=True))

    chars: list[ft.Control] = [k.section("Moje postavy", icon=ft.Icons.PERSON_OUTLINE)]
    if not app.order:
        chars.append(k.card(ft.Column([
            ft.Icon(ft.Icons.CASINO_OUTLINED, size=48, color=l.hi),
            k.text("Zatím žádná postava", size=19, weight=ft.FontWeight.BOLD, head=True),
            k.muted("Vytvoř si první postavu. Vybereš, jestli hraješ Dračí Hlídku, nebo Dračí doupě 1.6, "
                    "a aplikace se přizpůsobí pravidlům i vzhledem.", size=14, align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), padding=20))
    else:
        chars += [character_card(app, app.chars[cid]) for cid in app.order]
    chars.append(k.button("Nová postava" if app.order else "Vytvořit postavu", lambda e: open_generator(app),
                          primary=not app.order, icon=ft.Icons.ADD))

    gm: list[ft.Control] = [k.section("Vedu hru", icon=ft.Icons.WORKSPACE_PREMIUM_OUTLINED)]
    gm += [campaign_card(app, app.gm[cid]) for cid in app.gm_order]
    if not app.gm_order:
        gm.append(k.muted("Jako Pán jeskyně založíš kampaň bez postavy: hraje se u stolu přes Wi-Fi, nebo na tvém "
                          "vlastním serveru.", size=13))
    gm.append(ft.Row([k.button("Nová kampaň (PJ)", lambda e: propojeni.new_campaign(app), primary=False,
                               icon=ft.Icons.WORKSPACE_PREMIUM_OUTLINED, expand=1)]))
    gm.append(ft.Container(k.text("Přihlásit se jako PJ na tomto zařízení ›", size=13, weight=ft.FontWeight.BOLD,
                                  color=l.orn), on_click=lambda e: app.go("pj_login", login_done=None),
                           ink=True, padding=ft.Padding.symmetric(vertical=8), alignment=ft.Alignment.CENTER))

    controls += (chars + gm) if mode == "Hraju" else (gm + chars)
    controls.append(k.note("Stůl PJ a obsah příruček PJ se otevře jen Pánovi jeskyně. Hráči nic nevyplňují."))
    controls.append(backup.backup_card(app))
    controls.append(k.muted(f"Verze {VERSION}", size=12, align=ft.TextAlign.CENTER))
    return Screen("Tvoje postavy", [column(controls)])


def character_card(app, c: dict) -> ft.Control:
    """Karta postavy podle návrhu: kulatý odznak, jméno, rasa · povolání · úroveň, pruh se jménem hry, šipka.
    Smazání: podržet prst na kartě."""
    k = app.kit
    l = app.look
    own = theme.for_system(c["system"])
    r = SYS[c["system"]]
    avatar = avatar_ui.avatar(app, c, 56, 28, own.orn, own.bg2, border=3, font_family=k.hf)

    def delete(e):
        async def do():
            await app.delete_character(c["id"])
            app.render()
        app.confirm("Smazat postavu?", f"{c['name']} bude smazán i s deníkem a obrázky.", do)

    camp = c.get("campaign")
    bar_text = "DrD 1.6" if c["system"] == "drd" else r.SHORT
    if camp and camp.get("status") == "pending":
        bar_text += " · čeká na PJ"
    bar = ft.Container(ft.Text(bar_text, size=11, weight=ft.FontWeight.BOLD, color="#ffffff"), bgcolor=own.accent,
                       border=ft.Border.all(1, own.orn), border_radius=ft.BorderRadius.all(4),
                       padding=ft.Padding.symmetric(horizontal=8, vertical=3))
    body = ft.Row([
        avatar,
        ft.Column([
            k.text(c["name"], size=18, weight=ft.FontWeight.BOLD, head=True, max_lines=1),
            k.muted(f"{c['race']} · {c['cls']} · {c['level']}. úroveň", size=14, max_lines=1),
            bar,
        ], spacing=4, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=own.orn),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(body, padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                        border_radius=ft.BorderRadius.all(l.radius),
                        gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                                                   colors=[own.bg2, l.card], stops=[0.0, 0.7]),
                        border=ft.Border.all(1, own.frame), shadow=[ft.BoxShadow(blur_radius=12, color=own.glow)],
                        on_click=lambda e: app.open_character(c["id"]), on_long_press=delete, ink=True,
                        tooltip="Podrž prst pro smazání", data="char:" + c["id"])


def campaign_card(app, camp: dict) -> ft.Control:
    """Karta kampaně PJ: korunka, název, hra · sezení · hráči, čekající žádosti."""
    from .. import sync

    k = app.kit
    l = app.look
    own = theme.for_system(camp["system"])
    n = len(sync.players(camp))
    waiting = len(sync.players(camp, "pending"))
    game = "Dračí doupě 1.6" if camp["system"] == "drd" else "Dračí Hlídka"
    how = "u stolu" if sync.is_table(camp) else "server"
    col: list[ft.Control] = [k.text(camp["name"], size=17, weight=ft.FontWeight.BOLD, head=True, max_lines=1),
                             k.muted(f"{game} · sezení {camp['session']} · {n} {_hraci(n)} · {how}", size=13)]
    if waiting:
        col.append(ft.Row([ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, size=14, color=l.warn),
                           k.text(f"{waiting} čeká na schválení", size=12, weight=ft.FontWeight.BOLD, color=l.warn)],
                          spacing=4))
    crown = ft.Container(ft.Icon(ft.Icons.WORKSPACE_PREMIUM, size=26, color="#ffffff"), width=50, height=50,
                         alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(8),
                         gradient=ft.RadialGradient(colors=[own.accent2, own.accent]), border=ft.Border.all(2, own.orn))
    return ft.Container(
        ft.Row([crown, ft.Column(col, spacing=3, expand=True), ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=own.orn)],
               spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.all(12), border_radius=ft.BorderRadius.all(l.radius),
        gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                                   colors=[own.bg2, l.card], stops=[0.0, 0.75]),
        border=ft.Border.all(1, own.orn), shadow=[ft.BoxShadow(blur_radius=12, color=own.glow)],
        on_click=lambda e: app.open_gm(camp["id"]), ink=True, data="camp:" + camp["id"])


def _hraci(n: int) -> str:
    return "hráč" if n == 1 else "hráči" if 2 <= n <= 4 else "hráčů"


# --- generátor ---------------------------------------------------------------

def open_generator(app) -> None:
    app.ui.update({"gen_sys": app.ui.get("gen_sys") or "drd", "gen_mode": "auto", "gen_name": ""})
    reset_gen(app)
    app.go("generator")


def reset_gen(app) -> None:
    s = app.ui["gen_sys"]
    r = SYS[s]
    races = list(r.RACES) if s == "dh" else list(r.RACE_RANGES)
    classes = list(r.CLASSES)
    if app.ui.get("gen_race") not in races:
        app.ui["gen_race"] = races[0]
    if app.ui.get("gen_cls") not in classes:
        app.ui["gen_cls"] = classes[0]
    reroll(app)


def reroll(app) -> None:
    s, race, cls, mode = app.ui["gen_sys"], app.ui["gen_race"], app.ui["gen_cls"], app.ui["gen_mode"]
    if s == "dh":
        if mode == "auto":
            app.ui["gen_attrs"] = dh.generate_auto(race, cls)
        else:
            app.ui["gen_points"] = [4, 4, 4, 4, 4]
            app.ui["gen_attrs"] = dh.finalize(app.ui["gen_points"], race, cls)
    else:
        if mode == "auto":
            app.ui["gen_attrs"] = drd.generate_auto(race, cls)
        else:
            app.ui["gen_attrs"] = [sum(drd.attr_range(race, cls, i)) // 2 for i in range(5)]


def generator(app):
    from ..core import Screen

    k = app.kit
    l = app.look
    u = app.ui
    s = u["gen_sys"]
    r = SYS[s]
    races = list(r.RACES) if s == "dh" else list(r.RACE_RANGES)
    classes = list(r.CLASSES)
    manual = u["gen_mode"] == "manual"

    def set_sys(v):
        u["gen_sys"] = "dh" if v == dh.NAME else "drd"
        u["gen_mode"] = "auto"
        reset_gen(app)
        app.refresh()

    def set_race(v):
        u["gen_race"] = v
        reroll(app)
        app.refresh()

    def set_cls(v):
        u["gen_cls"] = v
        reroll(app)
        app.refresh()

    def set_mode(v):
        u["gen_mode"] = "manual" if v == "Ručně" else "auto"
        reroll(app)
        app.refresh()

    def on_name(e):
        u["gen_name"] = e.control.value

    name = ft.TextField(label="Jméno postavy", value=u.get("gen_name", ""), on_change=on_name,
                        border_color=l.frame, focused_border_color=l.hi, color=l.ink, cursor_color=l.hi,
                        filled=True, fill_color=l.bg)
    sl = theme.for_system(s)  # vlastnosti v barvách zvolené hry
    sk = Kit(sl, theme.head(sl, app.fonts))

    def sys_card(key: str) -> ft.Control:
        th = theme.for_system(key)
        on = key == s
        return ft.Container(ft.Stack([
            ft.Image(src=th.banner, fit=ft.BoxFit.COVER, left=0, right=0, top=0, bottom=0, opacity=0.65),
            ft.Container(left=0, right=0, bottom=0, height=60,
                         gradient=ft.LinearGradient(begin=ft.Alignment.BOTTOM_CENTER, end=ft.Alignment.TOP_CENTER,
                                                    colors=[th.bg, "#00000000"])),
            ft.Container(k.text(SYS[key].NAME, size=16, weight=ft.FontWeight.BOLD, head=True, color=th.ink),
                         left=10, bottom=8, right=8),
        ]), height=132, expand=1, bgcolor=th.bg, border_radius=ft.BorderRadius.all(l.radius),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(2 if on else 1, th.orn if on else th.frame),
            shadow=[ft.BoxShadow(blur_radius=16, color=th.glow)] if on else None,
            on_click=lambda e, key=key: set_sys(SYS[key].NAME), ink=True, data="gensys:" + key)

    rows: list[ft.Control] = []
    left = 0
    if s == "dh" and manual:
        left = dh.POINT_POOL - sum(u["gen_points"])
    if manual:
        for i, a in enumerate(r.ATTRS):
            val = u["gen_attrs"][i]
            if s == "drd":
                lo, hi = drd.attr_range(u["gen_race"], u["gen_cls"], i)
                n, add = drd.range_dice(lo, hi)
                sub = f"rozsah {lo}–{hi} ({n}k6{fmt(add) if add else ''})"
            else:
                sub = f"body {u['gen_points'][i]} + rodový {dh.RACES[u['gen_race']][i]}" + (
                    " + 3" if a in dh.CLASSES[u['gen_cls']] else "")
            rows.append(k.stepper(val, lambda e, i=i: step(app, i, -1), lambda e, i=i: step(app, i, +1),
                                  label=f"{a}  ·  oprava {fmt(r.bonus(val))}", sub=sub))
    boxes = ft.Row([
        sk.stat(a, u["gen_attrs"][i], fmt(r.bonus(u["gen_attrs"][i])),
                sub_color=(sl.accent2 if s == "dh" else sl.orn) if r.bonus(u["gen_attrs"][i]) > 0 else sl.muted)
        for i, a in enumerate(r.ATTRS)], spacing=6)

    if s == "dh":
        hint = (f"Rozděl {dh.POINT_POOL} bodů (do každé vlastnosti 1–6). Zbývá: {left}." if manual else
                "6× k6, nejnižší hod se škrtá, zbylé se rozdělí. Přičten rodový základ a +3 k dominantním vlastnostem.")
    else:
        hint = ("Zadej hodnoty, které jsi hodil fyzickými kostkami (v povoleném rozsahu)." if manual else
                "Vlastnosti hozeny podle tabulek rasy a povolání.")

    if s == "dh":
        hp = dh.hit_points(u["gen_attrs"])
        summary = f"Životy {hp} · hranice smrti {dh.death_threshold(u['gen_attrs'])} · peníze 1k10+30 zl"
    else:
        hp = drd.hit_points(u["gen_cls"], u["gen_attrs"])
        summary = f"Životy na 1. úrovni {hp} (základ {drd.HP_TABLE[u['gen_cls']][0]} + oprava ODL)"

    class_card: list[ft.Control] = []
    if s == "drd":
        from .character import class_abilities_card
        lvl = u.get("gen_lvl", 1)
        cls = u["gen_cls"]
        mains = []
        for a in drd.CLASS_RANGES[cls]:
            i = drd.ATTRS.index(a)
            lo, hi = drd.attr_range(u["gen_race"], cls, i)
            n, add = drd.range_dice(lo, hi)
            m = drd.RACE_MODS[u["gen_race"]][i]
            mains.append(ft.Container(ft.Column([
                k.muted(f"{a} · máš {u['gen_attrs'][i]}", size=12, weight=ft.FontWeight.BOLD),
                k.text(f"{lo}–{hi}", size=22, weight=ft.FontWeight.BOLD, head=True),
                k.muted(f"{n}k6{fmt(add) if add else ''}" + (f" (rasa {fmt(m)})" if m else ""), size=12),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER), expand=1, bgcolor=l.card2,
                border=ft.Border.all(1, l.border), border_radius=ft.BorderRadius.all(l.radius),
                padding=ft.Padding.symmetric(vertical=8, horizontal=4)))
        class_card = [k.section(f"Povolání {cls}", icon=ft.Icons.MENU_BOOK_OUTLINED), k.card(ft.Column([
            k.muted(drd.CLASS_DESC[cls], size=13),
            k.muted("ZÁKLADNÍ VLASTNOSTI POVOLÁNÍ", size=12, weight=ft.FontWeight.BOLD),
            ft.Row(mains, spacing=8),
            k.muted("SCHOPNOSTI NA ÚROVNI", size=12, weight=ft.FontWeight.BOLD),
            k.pills([str(n) for n in range(1, 6)], str(lvl),
                    lambda v: (u.update({"gen_lvl": int(v)}), app.refresh()), equal=True),
            class_abilities_card(app, cls, lvl, u["gen_attrs"]),
            k.muted(drd.class_note(cls), size=12),
        ], spacing=8))]

    can_create = not (s == "dh" and manual and left != 0)

    def create(e):
        c = model.create_character(s, u.get("gen_name", ""), u["gen_race"], u["gen_cls"], u["gen_attrs"])
        app.add_character(c)
        app.go("start")
        app.toast(f"Postava {c['name']} byla vytvořena.")

    attr_head = k.section("Vlastnosti", icon=ft.Icons.CASINO_OUTLINED,
                          trailing=None if manual else k.link("Hodit znovu", lambda e: (reroll(app), app.refresh())))
    controls = [
        k.muted("Vyber hru – aplikace se přizpůsobí pravidlům i vzhledem.", size=14),
        ft.Row([sys_card("drd"), sys_card("dh")], spacing=10),
        k.section("Jméno"), name,
        k.section("Rasa"), k.pills(races, u["gen_race"], set_race),
        k.section("Povolání"), k.pills(classes, u["gen_cls"], set_cls),
        attr_head,
        boxes,
        k.pills(["Podle pravidel", "Ručně"], "Ručně" if manual else "Podle pravidel", set_mode, wrap=False),
        k.muted(hint, size=12),
        *rows,
        k.muted(summary, size=13),
        *class_card,
        ft.Container(height=6),
        ft.Row([k.button("Vytvořit postavu" if can_create else f"Rozděl ještě {left} bodů", create,
                         icon=ft.Icons.CHECK, disabled=not can_create, expand=1, height=52)]),
    ]
    return Screen("Nová postava", [column(controls)])


def step(app, i: int, delta: int) -> None:
    u = app.ui
    if u["gen_sys"] == "dh":
        pts = list(u["gen_points"])
        nv = pts[i] + delta
        if nv < dh.POINT_MIN or nv > dh.POINT_MAX:
            return
        if delta > 0 and sum(pts) >= dh.POINT_POOL:
            return
        pts[i] = nv
        u["gen_points"] = pts
        u["gen_attrs"] = dh.finalize(pts, u["gen_race"], u["gen_cls"])
    else:
        lo, hi = drd.attr_range(u["gen_race"], u["gen_cls"], i)
        vals = list(u["gen_attrs"])
        vals[i] = max(lo, min(hi, vals[i] + delta))
        u["gen_attrs"] = vals
    app.refresh()
