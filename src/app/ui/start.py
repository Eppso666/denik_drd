"""Společné obrazovky: výběr postavy a generátor postavy."""
from __future__ import annotations

import hashlib
import os
import time

import flet as ft

from .. import model, sync, theme, version
from ..version import VERSION
from ..rules import dh, drd
from ..rules.common import fmt
from . import art, backup
from . import avatar as avatar_ui
from .kit import Kit, column

SYS = {"dh": dh, "drd": drd}


def uvod(app):
    """Úvod: kdo dnes jsi – Hráč, nebo Pán jeskyně (návrh z DRD_uprava.docx)."""
    from ..core import Screen

    k = app.kit
    l = app.look

    def tile(title: str, sub: str, picture: bytes, target: str) -> ft.Control:
        return ft.Container(ft.Column([
            ft.Container(ft.Image(src=picture, fit=ft.BoxFit.COVER, height=210), height=210,
                         clip_behavior=ft.ClipBehavior.HARD_EDGE),
            ft.Container(ft.Row([
                ft.Column([k.text(title, size=22, weight=ft.FontWeight.BOLD, head=True), k.muted(sub, size=13)],
                          spacing=2, expand=True),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=24, color=l.orn),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                gradient=k.grad(l.card2, l.card), border=ft.Border.only(top=ft.BorderSide(1, l.orn))),
        ], spacing=0), border_radius=ft.BorderRadius.all(8), clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(2, l.orn), shadow=k.glow(18), bgcolor=l.card,
            on_click=lambda e: app.go(target), ink=True, data="uvod:" + target)

    controls = [
        k.text("DENÍK DOBRODRUHA", size=12, weight=ft.FontWeight.BOLD, color=l.orn),
        k.muted("Kdo dnes jsi?", size=15),
        tile("Hráč", "Moje postavy a jejich deníky", art.party(), "start"),
        tile("Pán jeskyně", "Doupě pána jeskyně – moje příběhy", art.puppeteer(), "doupe"),
        k.muted(f"Verze {VERSION}", size=12, align=ft.TextAlign.CENTER),
    ]
    return Screen("Deník dobrodruha", [column(controls)])


def start(app):
    """Hráč – Deník dobrodruha: jen Moje postavy, nová postava a záloha."""
    from ..core import Screen

    k = app.kit
    l = app.look
    controls: list[ft.Control] = []
    seen = app.settings.get("seen_version")
    if seen != VERSION:
        news = version.news_since(seen) if app.order else []
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

    chars: list[ft.Control] = []
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

    controls.append(k.section("Moje postavy", icon=ft.Icons.PERSON_OUTLINE))
    controls += chars
    controls.append(backup.backup_card(app))
    controls.append(k.muted(f"Verze {VERSION}", size=12, align=ft.TextAlign.CENTER))
    return Screen("Deník dobrodruha", [column(controls)])


# --- Pán jeskyně: Doupě pána jeskyně ------------------------------------------

PW_ROUNDS = 60_000


def hash_password(password: str, salt: bytes | None = None) -> dict:
    """Heslo kampaně se neukládá – jen sůl a otisk (PBKDF2-SHA256)."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PW_ROUNDS)
    return {"salt": salt.hex(), "hash": digest.hex(), "rounds": PW_ROUNDS}


def check_password(camp: dict, password: str) -> bool:
    pw = camp.get("pw") or {}
    if not pw.get("salt"):
        return True
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(pw["salt"]),
                                 int(pw.get("rounds", PW_ROUNDS)))
    return digest.hex() == pw.get("hash")


def new_gm_campaign(system: str, name: str, password: str) -> dict:
    return {"id": model.new_id(), "name": name.strip()[:80] or "Nový příběh", "system": system, "session": 1,
            "code": sync.new_code(), "pw": hash_password(password), "created": time.time(),
            "members": [], "feed": [], "notes": [], "maps": [], "xp_pool": [], "combat": None, "outbox": []}


def doupe(app):
    """Pán jeskyně – Doupě pána jeskyně: Moje příběhy (kampaně chráněné heslem)."""
    from ..core import Screen

    k = app.kit
    cards = [campaign_card(app, app.gm[cid]) for cid in app.gm_order if cid in app.gm]
    controls: list[ft.Control] = [
        k.section("Moje příběhy", icon=ft.Icons.WORKSPACE_PREMIUM_OUTLINED),
        *(cards or [k.empty("Zatím žádný příběh. Založ první kampaň – dostane název a heslo.")]),
        k.button("Nový příběh (kampaň)", lambda e: new_campaign_dialog(app), primary=not cards,
                 icon=ft.Icons.WORKSPACE_PREMIUM_OUTLINED, height=48),
        k.note("Každou kampaň chrání její heslo – bez něj se Stůl PJ neotevře. Hráči heslo neznají; do kampaně "
               "se připojí jen kódem kampaně (propojení s hráči připravujeme)."),
    ]
    return Screen("Doupě pána jeskyně", [column(controls)])


def campaign_card(app, camp: dict) -> ft.Control:
    k = app.kit
    l = app.look
    own = theme.for_system(camp["system"])
    game = SYS[camp["system"]].NAME

    def delete(e):
        async def do():
            await app.delete_gm(camp["id"])
            app.render()
        app.confirm("Smazat kampaň?", f"„{camp['name']}“ bude smazána i s poznámkami PJ. Postavy hráčů zůstanou.",
                    do)

    badge = ft.Container(ft.Icon(ft.Icons.WORKSPACE_PREMIUM_OUTLINED, size=26, color="#ffffff"), width=50, height=50,
                         alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(8),
                         gradient=ft.RadialGradient(colors=[own.accent2, own.accent]), border=ft.Border.all(2, own.orn))
    n = len([m for m in camp.get("members") or [] if m.get("status", "approved") == "approved"])
    body = ft.Row([
        badge,
        ft.Column([
            k.text(camp["name"], size=17, weight=ft.FontWeight.BOLD, head=True, max_lines=2),
            k.muted(f"{game} · sezení {camp.get('session', 1)} · {n} hráč{'' if n == 1 else ('i' if 1 < n < 5 else 'ů')}",
                    size=13),
            ft.Row([ft.Icon(ft.Icons.LOCK_OUTLINE, size=13, color=l.orn), k.muted("chráněno heslem", size=12)],
                   spacing=4),
        ], spacing=3, expand=True),
        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=22, color=own.orn),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(body, padding=12, border_radius=ft.BorderRadius.all(l.radius),
                        gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                                                   colors=[own.bg2, l.card], stops=[0.0, 0.75]),
                        border=ft.Border.all(1, own.orn), shadow=[ft.BoxShadow(blur_radius=12, color=own.glow)],
                        on_click=lambda e: open_campaign(app, camp), on_long_press=delete, ink=True,
                        tooltip="Podrž prst pro smazání", data="camp:" + camp["id"])


def new_campaign_dialog(app) -> None:
    games = [drd.NAME, dh.NAME]

    def save(v):
        name = (v.get("name") or "").strip()
        pw, pw2 = v.get("pw") or "", v.get("pw2") or ""
        if not name:
            app.toast("Vyplň název kampaně.")
            return
        if len(pw) < 4:
            app.toast("Heslo musí mít aspoň 4 znaky.")
            return
        if pw != pw2:
            app.toast("Hesla se neshodují.")
            return
        system = "dh" if v.get("game") == dh.NAME else "drd"
        camp = new_gm_campaign(system, name, pw)
        app.add_gm(camp)
        app.open_gm(camp["id"])
        app.toast(f"Kampaň {camp['name']} založena. Kód pro hráče {camp['code']}.")

    app.form("Nová kampaň", [
        ("game", "Hra", games[0], "choice", games),
        ("name", "Název kampaně", "", "text"),
        ("pw", "Heslo kampaně", "", "password"),
        ("pw2", "Heslo znovu", "", "password"),
        ("hint", "", "Heslo chrání Doupě pána jeskyně – poznámky, bestiář PJ a nástroje. Hráči ho neznají; "
                     "do kampaně se připojí kódem. Zapomenuté heslo nejde obnovit.", "info"),
    ], save, save_label="Založit")


def open_campaign(app, camp: dict) -> None:
    """Otevření kampaně: po spuštění aplikace se vždy ptá na heslo."""
    if camp["id"] in app.gm_unlocked:
        app.open_gm(camp["id"])
        return

    def save(v):
        if check_password(camp, v.get("pw") or ""):
            app.open_gm(camp["id"])
        else:
            app.toast("Špatné heslo.")
    app.form(camp["name"], [("info", "", "Zadej heslo kampaně. Bez něj se Doupě pána jeskyně neotevře.", "info"),
                            ("pw", "Heslo kampaně", "", "password")], save, save_label="Otevřít")


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
        n_abil = sum(1 for a in drd.class_abilities(cls, lvl, u["gen_attrs"]) if not a["locked"])
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
            k.framed(ft.Column([
                ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=18, color=l.orn),
                        k.text(f"{cls} na {lvl}. úrovni", size=15, weight=ft.FontWeight.BOLD, head=True, expand=True),
                        k.muted(f"{n_abil} schopnost{'' if n_abil == 1 else ('i' if 1 < n_abil < 5 else 'í')}",
                                size=12)], spacing=8),
                class_abilities_card(app, cls, lvl, u["gen_attrs"], new_at=lvl),
                *([k.muted(f"Schopnosti {lvl + 1}.–5. úrovně se ukážou po zvolení vyšší úrovně.", size=12)]
                  if lvl < 5 else []),
            ], spacing=8), padding=10, glow=True),
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
