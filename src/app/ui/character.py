"""Obrazovky postavy: přehled, postup na úroveň, dovednosti / schopnosti."""
from __future__ import annotations

import copy

import flet as ft

from .. import model
from ..rules import dh, drd
from ..rules.common import fmt
from .kit import column


def postava(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"

    initials = "".join(p[0] for p in c["name"].split()[:2]).upper() or "?"
    avatar = ft.Container(
        ft.Text(initials, size=24, weight=ft.FontWeight.BOLD, color=l.accent, font_family=k.hf),
        width=68, height=68, alignment=ft.Alignment.CENTER, bgcolor=l.card2 if is_dh else l.card,
        border=ft.Border.all(2 if is_dh else 3, l.accent),
        border_radius=ft.BorderRadius.all(18 if is_dh else 34),
    )
    xp = f"Zkušenosti {c['xp']}" + (f" / {c['xp_next']}" if c.get("xp_next") else "")
    header = ft.Row([
        avatar,
        ft.Column([
            k.text(c["name"], size=21, weight=ft.FontWeight.BOLD, head=True, max_lines=2),
            k.muted(f"{c['race']} · {c['cls']} · {c['level']}. úroveň", size=14),
            k.muted(xp, size=12),
        ], spacing=2, expand=True),
        k.button("Postup", lambda e: open_postup(app), primary=False, height=44, icon=ft.Icons.TRENDING_UP),
    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def change_hp(sign: int):
        def save(v):
            n = int(v["n"])
            c["hp"] = max(c.get("death", 0) if is_dh else -99, min(c["hp_max"], c["hp"] + sign * n))
            model.add_history(c, "Zranění" if sign < 0 else "Léčení", f"{'−' if sign < 0 else '+'}{n}")
            app.save(c)
            app.refresh()
        app.form("Zranění" if sign < 0 else "Léčení", [("n", "Počet životů", 1, "int")], save,
                 save_label="Potvrdit")

    def change_mana(sign: int):
        def save(v):
            c["mana"] = max(0, min(c["mana_max"], c["mana"] + sign * int(v["n"])))
            app.save(c)
            app.refresh()
        app.form(f"{c.get('mana_name') or 'Mana'}: {'utratit' if sign < 0 else 'doplnit'}",
                 [("n", "Množství", 1, "int")], save, save_label="Potvrdit")

    def rest(e):
        if is_dh:
            c["mana"] = c["mana_max"]
            app.toast("Mana doplněna na maximum.")
        else:
            c["hp"] = min(c["hp_max"], c["hp"] + 2)
            app.toast("Odpočinek: +2 životy.")
        app.save(c)
        app.refresh()

    gauges: list[ft.Control] = [
        k.gauge("Životy", c["hp"], c["hp_max"], l.hp, f" · hr. smrti {c['death']}" if is_dh else ""),
    ]
    if c.get("mana_max", 0) > 0:
        gauges.append(k.gauge(c.get("mana_name") or "Mana", c["mana"], c["mana_max"], l.mana))
    btn_row = [k.button("Zranit", lambda e: change_hp(-1), primary=False, expand=1, height=44),
               k.button("Léčit", lambda e: change_hp(+1), primary=False, expand=1, height=44),
               k.button("Odpočinek", rest, primary=False, expand=1, height=44)]
    gauges.append(ft.Row(btn_row, spacing=8))
    if c.get("mana_max", 0) > 0:
        gauges.append(ft.Row([k.button(f"− {c.get('mana_name') or 'Mana'}", lambda e: change_mana(-1), primary=False,
                                       expand=1, height=40),
                              k.button(f"+ {c.get('mana_name') or 'Mana'}", lambda e: change_mana(+1), primary=False,
                                       expand=1, height=40)], spacing=8))

    attrs = ft.Row([
        k.stat(a, c["attrs"][i], fmt(r.bonus(c["attrs"][i])),
               sub_color=l.accent if r.bonus(c["attrs"][i]) > 0 else l.muted)
        for i, a in enumerate(r.ATTRS)
    ], spacing=6)

    # boj
    fight_rows: list[ft.Control] = []
    for w in model.weapons(c):
        uc = r.weapon_uc(w, c["attrs"])
        ocv = model.oc(c, w)
        stats = (f"útočnost {w.get('attack', 0)} · zranění {fmt(int(w.get('damage', 0)))} · obrana {w.get('defense', 0)}"
                 if is_dh else f"SZ {w.get('attack', 0)} · útočnost {fmt(int(w.get('damage', 0)))} · OZ {w.get('defense', 0)}")
        fight_rows.append(ft.Row([
            ft.Column([k.text(w["name"], size=15, weight=ft.FontWeight.W_600),
                       k.muted(stats + (" · střelná" if w.get("ranged") else ""))], spacing=2, expand=True),
            ft.Container(k.stat("ÚČ", uc), width=56), ft.Container(k.stat("OČ", ocv), width=56),
        ], spacing=8))
    arm = model.armor_quality(c)
    shield = model.shield_bonus(c)
    if is_dh:
        fight_rows.append(k.muted(f"ZO {dh.base_defense(c['attrs'], arm)} (OBR + zbroj {arm}) · štít {fmt(shield)} · "
                                  f"iniciativa OBR {fmt(dh.bonus(c['attrs'][1]))} + k6"))
    else:
        fight_rows.append(k.muted(f"Kvalita zbroje {arm} · štít {fmt(shield)} · útok ÚČ + k6+, obrana OČ + k6+"))

    # dovednosti / schopnosti
    if is_dh:
        skills = sorted(c["skills"], key=lambda s: -s["level"])[:5]
        srows = [k.row_item(s["name"], f"{s['attr']} · stupeň {s['level']}",
                            badge="VLASTNÍ" if s.get("kind") == "Vlastní" else None,
                            on_click=lambda e, s=s: app.go("kostky", dice_tab="Dovednost", dice_skill=s["name"]))
                 for s in skills]
        sec_title = "Dovednosti"
    else:
        abil = c["abilities"][:5]
        srows = [k.row_item(a["name"], f"{a['pct']} %", badge="VLASTNÍ" if a.get("kind") == "Vlastní" else None,
                            on_click=lambda e, a=a: app.go("kostky", dice_tab="Schopnost", dice_ability=a["name"]))
                 for a in abil]
        sec_title = "Schopnosti a dovednosti"
    skills_block = k.list_card(srows) if srows else k.empty("Zatím žádné. Přidej je přes „Upravit“.")

    controls = [
        header,
        k.card(ft.Column(gauges, spacing=10)),
        k.section("Vlastnosti"),
        attrs,
        k.section("Boj", ft.TextButton("Souboj", on_click=lambda e: app.go("souboj"))),
        k.card(ft.Column(fight_rows, spacing=10)),
        k.section(sec_title, ft.TextButton("Upravit", on_click=lambda e: app.go("dovednosti"))),
        skills_block,
    ]
    actions = [ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=l.ink, tooltip="Upravit postavu",
                             on_click=lambda e: edit_character(app))]
    return Screen(r.NAME, [column(controls)], actions=actions)


def edit_character(app) -> None:
    c = app.char
    fields = [("name", "Jméno", c["name"], "text"), ("race", "Rasa", c["race"], "text"),
              ("cls", "Povolání", c["cls"], "text"), ("xp", "Zkušenosti", c["xp"], "int"),
              ("xp_next", "Zkušenosti na další úroveň", c.get("xp_next", 0), "int"),
              ("hp", "Aktuální životy", c["hp"], "int"),
              ("mana_name", "Název many (Mana, Adrenalin, Magenergie…)", c.get("mana_name", ""), "text"),
              ("mana", "Aktuální mana", c["mana"], "int"), ("mana_max", "Maximum many", c["mana_max"], "int")]
    if c["system"] == "dh":
        fields.append(("death", "Hranice smrti", c["death"], "int"))

    def save(v):
        c.update(v)
        c["hp"] = min(c["hp"], c["hp_max"])
        c["mana"] = min(c["mana"], c["mana_max"])
        app.save(c)
        app.refresh()
    app.form("Upravit postavu", fields, save)


# --- postup na úroveň ----------------------------------------------------------

def open_postup(app) -> None:
    c = app.char
    app.ui["lvl"] = {"level": c["level"] + 1, "hp_max": c["hp_max"], "mana_max": c["mana_max"],
                     "attrs": list(c["attrs"]), "skill_points": c.get("skill_points", 0),
                     "xp_next": c.get("xp_next", 0), "rolled": None}
    app.go("postup")


def postup(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"
    w = app.ui.setdefault("lvl", None)
    if w is None:
        open_postup(app)
        w = app.ui["lvl"]

    def adj(key, delta, lo=0):
        def h(e):
            w[key] = max(lo, w[key] + delta)
            app.refresh()
        return h

    def adj_attr(i, delta):
        def h(e):
            w["attrs"][i] = max(1, w["attrs"][i] + delta)
            app.refresh()
        return h

    def diff(new, old):
        return "beze změny" if new == old else f"{old} – {new}"

    rows = [
        k.stepper(w["level"], adj("level", -1, 1), adj("level", +1), label="Úroveň", sub=diff(w["level"], c["level"])),
        k.stepper(w["hp_max"], adj("hp_max", -1, 1), adj("hp_max", +1), label="Maximum životů",
                  sub=diff(w["hp_max"], c["hp_max"])),
        k.stepper(w["mana_max"], adj("mana_max", -1), adj("mana_max", +1),
                  label=f"Maximum: {c.get('mana_name') or 'mana'}", sub=diff(w["mana_max"], c["mana_max"])),
    ]
    if is_dh:
        rows.append(k.stepper(w["skill_points"], adj("skill_points", -1), adj("skill_points", +1),
                              label="Dovednostní body", sub="utratíš je v Dovednostech"))
        banner = ("Na každé třetí úrovni můžeš zvýšit dvě vlastnosti o 1. Každou dovednost lze za úroveň zlepšit "
                  "nejvýš o jeden stupeň. Hodnoty uprav podle příručky nebo dohody s PJ.")
    else:
        cls = c["cls"] if c["cls"] in drd.HP_TABLE else "Válečník"
        _, sides, add = drd.HP_TABLE[cls]

        def roll_hp(e):
            kk, gain = drd.level_hp_roll(cls, c["attrs"])
            w["hp_max"] += gain
            w["rolled"] = f"k{sides} = {kk}{fmt(add) if add else ''} {fmt(drd.bonus(c['attrs'][2]))} ODL – +{gain}"
            app.refresh()
        rows.append(k.button(f"Hodit k{sides}{fmt(add) if add else ''} + oprava ODL na přírůstek životů", roll_hp,
                             primary=False, icon=ft.Icons.CASINO_OUTLINED))
        if w.get("rolled"):
            rows.append(k.muted(f"Hod: {w['rolled']}"))
        banner = ("Vlastnosti se v DrD 1.6 při postupu běžně nemění. Ruční úprava je pro případy, kdy to povolí PJ "
                  "(kouzlo, lektvar, kletba). Přírůstek životů je vždy alespoň 1.")

    attr_cells = []
    for i, a in enumerate(r.ATTRS):
        changed = w["attrs"][i] != c["attrs"][i]
        attr_cells.append(ft.Container(ft.Column([
            k.muted(a, size=11, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.Icons.ADD, on_click=adj_attr(i, +1), icon_color=l.ink, tooltip=f"Zvýšit {a}"),
            k.text(w["attrs"][i], size=20, weight=ft.FontWeight.BOLD, head=True, color=l.accent if changed else l.ink),
            ft.IconButton(ft.Icons.REMOVE, on_click=adj_attr(i, -1), icon_color=l.ink, tooltip=f"Snížit {a}"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0), expand=1, bgcolor=l.card,
            border=ft.Border.all(2 if changed else 1, l.accent if changed else l.border),
            border_radius=ft.BorderRadius.all(l.radius), padding=ft.Padding.symmetric(vertical=6)))

    def save(e):
        gain = w["hp_max"] - c["hp_max"]
        old_odo = c["attrs"][2]
        c["level"] = w["level"]
        c["hp_max"] = w["hp_max"]
        c["hp"] = max(-99, min(c["hp_max"], c["hp"] + max(0, gain)))
        c["mana_max"] = w["mana_max"]
        c["mana"] = min(c["mana"], c["mana_max"])
        c["attrs"] = list(w["attrs"])
        if is_dh:
            c["skill_points"] = w["skill_points"]
            if c["attrs"][2] != old_odo:
                c["death"] = dh.death_threshold(c["attrs"])
        model.add_history(c, "Postup", f"{c['level']}. úroveň")
        app.save(c)
        app.ui["lvl"] = None
        app.toast(f"Uloženo: {c['level']}. úroveň")
        app.go("postava")

    controls = [
        k.card(k.text(banner, size=14), bg=l.card2),
        k.card(ft.Column(rows, spacing=10)),
        k.section("Vlastnosti"),
        ft.Row(attr_cells, spacing=6),
        k.button("Uložit postup", save),
    ]
    return Screen("Postup na úroveň", [column(controls)])


# --- dovednosti / schopnosti -----------------------------------------------------

def dovednosti(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    rows: list[ft.Control] = []
    if is_dh:
        for s in sorted(c["skills"], key=lambda s: (-s["level"], s["name"])):
            rows.append(k.row_item(
                s["name"], f"{s['attr']} · stupeň {s['level']}", sub=s.get("kind"),
                badge="VLASTNÍ" if s.get("kind") == "Vlastní" else None, on_click=lambda e, s=s: edit_skill(app, s),
                trailing=ft.IconButton(ft.Icons.CASINO_OUTLINED, icon_color=l.accent, tooltip="Hodit",
                                       on_click=lambda e, s=s: app.go("kostky", dice_tab="Dovednost",
                                                                      dice_skill=s["name"]))))
        info = (f"Dovednostní body: {c.get('skill_points', 0)}. Za 1 bod se naučíš novou dovednost na 1. stupeň. "
                "Hod: 1k10 + oprava vlastnosti + stupeň musí překonat obtížnost.")
    else:
        for a in c["abilities"]:
            rows.append(k.row_item(
                a["name"], f"{a['pct']} %", sub=(a.get("kind") or "") + (f" · oprava {a['attr']}" if a.get("attr") else ""),
                badge="VLASTNÍ" if a.get("kind") == "Vlastní" else None, on_click=lambda e, a=a: edit_ability(app, a),
                trailing=ft.IconButton(ft.Icons.CASINO_OUTLINED, icon_color=l.accent, tooltip="Hodit k%",
                                       on_click=lambda e, a=a: app.go("kostky", dice_tab="Schopnost",
                                                                      dice_ability=a["name"]))))
        info = ("Schopnosti povolání (např. zlodějské činnosti, stopování) a vlastní dovednosti podle domácích "
                "pravidel. Hod: k% musí padnout pod šanci nebo na ni.")
    controls = [
        k.card(k.muted(info, size=14)),
        k.list_card(rows) if rows else k.empty("Zatím prázdné."),
    ]
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=l.accent, foreground_color=l.on_accent,
                                  on_click=lambda e: (edit_skill(app, None) if is_dh else edit_ability(app, None)),
                                  tooltip="Přidat")
    return Screen("Dovednosti" if is_dh else "Schopnosti", [column(controls)], fab=fab)


def edit_skill(app, s: dict | None) -> None:
    c = app.char
    names = list(dh.SKILLS) + ["(vlastní – vyplň název)"]
    fields = [
        ("preset", "Základní dovednost", s["name"] if s and s["name"] in dh.SKILLS else names[-1], "choice", names),
        ("name", "Vlastní název", "" if s is None or s["name"] in dh.SKILLS else s["name"], "text"),
        ("attr", "Vlastnost", s["attr"] if s else "OBR", "choice", dh.ATTRS),
        ("level", "Stupeň", s["level"] if s else 1, "int"),
        ("kind", "Druh", s.get("kind", "Vlastní") if s else "Vlastní", "choice", ["Blízká", "Obecná", "Vlastní"]),
    ]

    def save(v):
        name = v["name"].strip() if v["preset"] == names[-1] else v["preset"]
        if not name:
            app.toast("Vyplň název dovednosti.")
            return
        data = {"name": name, "attr": v["attr"] or "OBR", "level": max(0, int(v["level"])), "kind": v["kind"] or "Vlastní"}
        if s is None:
            if v["preset"] != names[-1] and v["attr"] == "OBR":
                data["attr"] = dh.SKILLS.get(name, "OBR")
            c["skills"].append(data)
            if c.get("skill_points", 0) > 0:
                c["skill_points"] -= 1
        else:
            s.update(data)
        app.save(c)
        app.refresh()

    def delete():
        c["skills"].remove(s)
        app.save(c)
        app.refresh()

    app.form("Nová dovednost" if s is None else "Upravit dovednost", fields, save,
             on_delete=delete if s is not None else None)


def edit_ability(app, a: dict | None) -> None:
    c = app.char
    fields = [
        ("name", "Název", a["name"] if a else "", "text"),
        ("pct", "Šance (%)", a["pct"] if a else 40, "int"),
        ("attr", "Přičíst 5 × oprava vlastnosti (volitelné)", a.get("attr", "Žádná") if a else "Žádná", "choice",
         ["Žádná"] + drd.ATTRS),
        ("kind", "Druh", a.get("kind", "Vlastní") if a else "Vlastní", "choice", ["Schopnost povolání", "Vlastní"]),
    ]

    def save(v):
        if not v["name"].strip():
            app.toast("Vyplň název.")
            return
        data = {"name": v["name"].strip(), "pct": max(1, min(99, int(v["pct"]))),
                "attr": None if v["attr"] in (None, "Žádná") else v["attr"], "kind": v["kind"] or "Vlastní"}
        if a is None:
            c["abilities"].append(data)
        else:
            a.update(data)
        app.save(c)
        app.refresh()

    def delete():
        c["abilities"].remove(a)
        app.save(c)
        app.refresh()

    app.form("Nová schopnost" if a is None else "Upravit schopnost", fields, save,
             on_delete=delete if a is not None else None)


def ability_chance(c: dict, a: dict) -> int:
    base = int(a["pct"])
    if a.get("attr") in drd.ATTRS:
        base += 5 * drd.bonus(c["attrs"][drd.ATTRS.index(a["attr"])])
    return max(1, min(99, base))


_ = copy
