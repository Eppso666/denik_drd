"""Kostky a souboj. Každá hra má vlastní sadu kostek a vlastní typy hodů."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules import dh, drd
from ..rules.common import d, fmt, open_d6, roll_expr
from .character import ability_chance
from .kit import column


def _push(app, label: str, value, detail: str, color: str) -> None:
    c = app.char
    app.ui["dice_last"] = {"label": label, "value": str(value), "detail": detail, "color": color,
                           "char": c["id"]}
    model.add_history(c, label.capitalize(), str(value))
    app.save(c)
    app.refresh()


def _result_card(app) -> ft.Control:
    k = app.kit
    l = app.look
    last = app.ui.get("dice_last")
    if not last or last.get("char") != app.char["id"]:
        last = {"label": "VYBER A HOĎ", "value": "–", "detail": "Zvol, na co házíš", "color": l.ink}
    return k.card(ft.Column([
        k.muted(last["label"].upper(), size=12, weight=ft.FontWeight.BOLD),
        k.text(last["value"], size=54, weight=ft.FontWeight.BOLD, head=True, color=last["color"]),
        k.muted(last["detail"], size=14, align=ft.TextAlign.CENTER),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2), padding=16)


def _history(app) -> ft.Control:
    k = app.kit
    hist = app.char.get("history", [])[:5]
    if not hist:
        return ft.Container()
    return ft.Column([k.section("Historie"),
                      k.list_card([k.row_item(h["label"], h["value"]) for h in hist])], spacing=8)


def _free_dice(app, sides_list: list[str]) -> ft.Control:
    k = app.kit
    l = app.look
    buttons = []
    for name in sides_list:
        def roll(e, name=name):
            if name == "k6+":
                rolls = open_d6()
                _push(app, "k6+", sum(rolls), "Hody: " + " + ".join(map(str, rolls)) if len(rolls) > 1 else "Jeden hod",
                      l.accent)
            elif name == "k%":
                _push(app, "k%", d(100), "Procentový hod (1–100)", l.accent)
            else:
                n = int(name[1:])
                _push(app, name, d(n), f"Rozsah 1–{n}", l.accent)
        buttons.append(ft.Container(
            k.text(name, size=24, weight=ft.FontWeight.BOLD, head=True, align=ft.TextAlign.CENTER),
            height=76, expand=1, alignment=ft.Alignment.CENTER, bgcolor=l.card,
            border=ft.Border.all(1, l.border), border_radius=ft.BorderRadius.all(l.radius), on_click=roll, ink=True))
    return ft.Row(buttons, spacing=8)


def _weapon_tab(app, exploding: bool) -> list[ft.Control]:
    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    ws = model.weapons(c)
    wi = min(app.ui.get("dice_weapon", 0), len(ws) - 1)
    rows = []
    for idx, w in enumerate(ws):
        uc = r.weapon_uc(w, c["attrs"])
        rows.append(k.card(ft.Row([
            ft.Column([k.text(w["name"], size=15, weight=ft.FontWeight.W_600),
                       k.muted("střelná" if w.get("ranged") else "boj tváří v tvář")], spacing=2, expand=True),
            k.text(f"ÚČ {uc}", size=20, weight=ft.FontWeight.BOLD, head=True),
        ]), accent=idx == wi, on_click=lambda e, idx=idx: app.go("kostky", dice_weapon=idx), padding=12))
    w = ws[wi]
    uc = r.weapon_uc(w, c["attrs"])

    def attack(e):
        rolls = open_d6() if exploding else [d(6)]
        total = uc + sum(rolls)
        _push(app, f"Útok · {w['name']}", total, f"ÚČ {uc} + {'k6+' if exploding else 'k6'} ({roll_expr(rolls)})",
              l.accent)

    out = rows + [
        k.muted(f"Útok = ÚČ + {'k6+ (šestka se hází znovu)' if exploding else 'k6'}. Obránce hází OČ + "
                f"{'k6+' if exploding else 'k6'}; zasáhneš, když máš víc."),
        k.button(f"Hodit útok · {w['name']}", attack),
        k.button("Otevřít souboj se soupeřem", lambda e: app.go("souboj"), primary=False),
    ]
    if c["system"] == "dh":
        def toggle(e):
            app.settings["dh_exploding"] = e.control.value
            app.save(settings=True)
            app.refresh()
        out.insert(len(rows), ft.Switch(label="Šestka se hází znovu (k6+)", value=exploding, active_color=l.accent,
                                        on_change=toggle))
    return out


def kostky(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    tabs = ["Dovednost", "Zbraň", "Volný hod"] if is_dh else ["Zbraň", "Schopnost", "Past", "Volný hod"]
    tab = app.ui.get("dice_tab")
    if tab not in tabs:
        tab = tabs[0]

    body: list[ft.Control] = []
    if tab == "Dovednost":
        sel = app.ui.get("dice_skill")
        options = [s["name"] for s in c["skills"]]
        if sel not in options and sel not in dh.ATTRS:
            sel = options[0] if options else "OBR"
        diff = app.ui.get("dice_diff", 8)
        adv = app.ui.get("dice_adv", 0)
        rows = []
        for s in sorted(c["skills"], key=lambda s: (-s["level"], s["name"])):
            b = dh.bonus(c["attrs"][dh.ATTRS.index(s["attr"])])
            rows.append(k.card(ft.Row([
                ft.Column([k.text(s["name"], size=15, weight=ft.FontWeight.W_600),
                           k.muted(f"{s['attr']} {fmt(b)} · stupeň {s['level']}")], spacing=2, expand=True),
                k.text(fmt(b + s["level"]), size=18, weight=ft.FontWeight.BOLD, head=True),
            ]), accent=s["name"] == sel, padding=10,
                on_click=lambda e, n=s["name"]: app.go("kostky", dice_skill=n)))
        body += [k.muted("NA CO HÁZÍŠ", size=12, weight=ft.FontWeight.BOLD), *rows,
                 k.muted("…nebo jen na vlastnost bez dovednosti:", size=13),
                 k.pills(dh.ATTRS, sel if sel in dh.ATTRS else "", lambda v: app.go("kostky", dice_skill=v), equal=True),
                 k.stepper(diff, lambda e: app.go("kostky", dice_diff=max(0, diff - 1)),
                           lambda e: app.go("kostky", dice_diff=diff + 1), label="Obtížnost / nebezpečnost",
                           sub="určí PJ; výsledek ji musí překonat"),
                 k.pills(["Nevýhoda −5", "Bez úpravy", "Výhoda +5"], ["Nevýhoda −5", "Bez úpravy", "Výhoda +5"][adv + 1],
                         lambda v: app.go("kostky", dice_adv={"Nevýhoda −5": -1, "Bez úpravy": 0}.get(v, 1)), equal=True)]

        def roll_skill(e):
            if sel in dh.ATTRS:
                b, lvl, name, attr = dh.bonus(c["attrs"][dh.ATTRS.index(sel)]), 0, sel, sel
            else:
                s = next(s for s in c["skills"] if s["name"] == sel)
                b, lvl, name, attr = dh.bonus(c["attrs"][dh.ATTRS.index(s["attr"])]), s["level"], s["name"], s["attr"]
            kk, total, ok = dh.check(b, lvl, diff, adv)
            mod = f" {fmt(adv * dh.ADVANTAGE)}" if adv else ""
            _push(app, f"Ověření · {name}", total,
                  f"k10 ({kk}) {fmt(b)} {attr}" + (f" + stupeň {lvl}" if lvl else "") + mod +
                  f" – {'Úspěch' if ok else 'Neúspěch'} (obtížnost {diff})", l.ok if ok else l.bad)
        body.append(k.button(f"Hodit k10 · {sel}", roll_skill))

    elif tab == "Zbraň":
        body += _weapon_tab(app, app.settings.get("dh_exploding", True) if is_dh else True)

    elif tab == "Schopnost":
        abil = c["abilities"]
        if not abil:
            body.append(k.empty("Zatím nemáš žádné schopnosti v %. Přidej je v Postava – Schopnosti."))
            body.append(k.button("Přidat schopnost", lambda e: app.go("dovednosti"), primary=False))
        else:
            sel = app.ui.get("dice_ability")
            names = [a["name"] for a in abil]
            if sel not in names:
                sel = names[0]
            pm = app.ui.get("dice_pm", 0)
            for a in abil:
                ch = ability_chance(c, a)
                body.append(k.card(ft.Row([k.text(a["name"], size=15, weight=ft.FontWeight.W_600, expand=True),
                                           k.text(f"{ch} %", size=18, weight=ft.FontWeight.BOLD, head=True)]),
                                   accent=a["name"] == sel, padding=12,
                                   on_click=lambda e, n=a["name"]: app.go("kostky", dice_ability=n)))
            a = next(a for a in abil if a["name"] == sel)
            chance = max(1, min(99, ability_chance(c, a) + pm))
            body.append(k.stepper(f"{fmt(pm)} %", lambda e: app.go("kostky", dice_pm=pm - 5),
                                  lambda e: app.go("kostky", dice_pm=pm + 5), label="Úprava od PJ"))

            def roll_pct(e):
                p, ok = drd.percent(chance)
                _push(app, a["name"], p, f"{'Úspěch' if ok else 'Neúspěch'} – padlo {p}, šance {chance} %",
                      l.ok if ok else l.bad)
            body.append(k.button(f"Hodit k% · šance {chance} %", roll_pct))

    elif tab == "Past":
        ti = app.ui.get("dice_trap_attr", "OBR")
        danger = app.ui.get("dice_danger", 6)
        body += [k.muted("Vlastnost, proti které past působí", size=13),
                 k.pills([f"{a} {fmt(drd.bonus(c['attrs'][i]))}" for i, a in enumerate(drd.ATTRS)],
                         next((f"{a} {fmt(drd.bonus(c['attrs'][i]))}" for i, a in enumerate(drd.ATTRS) if a == ti), ""),
                         lambda v: app.go("kostky", dice_trap_attr=v.split()[0]), equal=True),
                 k.stepper(danger, lambda e: app.go("kostky", dice_danger=max(1, danger - 1)),
                           lambda e: app.go("kostky", dice_danger=danger + 1), label="Nebezpečnost pasti",
                           sub="hod musí být stejný nebo vyšší")]

        def roll_trap(e):
            b = drd.bonus(c["attrs"][drd.ATTRS.index(ti)])
            kk, total, ok = drd.trap(b, danger)
            _push(app, f"Past · {ti}", total, f"k10 ({kk}) {fmt(b)} – {'štěstí, odolal' if ok else 'smůla, past zasáhla'}"
                  f" (nebezpečnost {danger})", l.ok if ok else l.bad)
        body.append(k.button("Hodit proti pasti (k10)", roll_trap))

    else:
        r = model.rules(c["system"])
        body += [_free_dice(app, r.DICE),
                 k.muted("Dračí Hlídka: k6 pro boj, k10 pro dovednosti, kouzla a pasti. Procentový hod se nepoužívá."
                         if is_dh else "Dračí doupě 1.6: k6+ v boji, k10 proti pastem, k% u schopností."), ]

    controls = [_result_card(app), k.pills(tabs, tab, lambda v: app.go("kostky", dice_tab=v), equal=True),
                *body, _history(app)]
    return Screen("Kostky", [column(controls)])


# --- souboj --------------------------------------------------------------------

def _default_foe(app) -> dict:
    sys = app.char["system"]
    best = app.bestiary.get(sys, [])
    if best:
        return foe_from_beast(best[0])
    return {"name": "Soupeř", "uc": 3, "oc": 3, "hp": 10, "hp_max": 10, "dmg": 0}


def foe_from_beast(b: dict) -> dict:
    hp = int(b.get("hp", 10) or 10)
    return {"name": b.get("name", "Soupeř"), "uc": int(b.get("uc", 0)), "oc": int(b.get("oc", 0)), "hp": hp,
            "hp_max": hp, "dmg": int(b.get("dmg", 0))}


def souboj(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"
    exploding = app.settings.get("dh_exploding", True) if is_dh else True
    foe = app.ui.get("foe")
    if not foe or foe.get("sys") != c["system"]:
        foe = _default_foe(app)
        foe["sys"] = c["system"]
        app.ui["foe"] = foe
        app.ui["fight_log"] = []
        app.ui["round"] = 1
    log = app.ui.setdefault("fight_log", [])
    ws = model.weapons(c)
    wi = min(app.ui.get("dice_weapon", 0), len(ws) - 1)
    w = ws[wi]
    uc = r.weapon_uc(w, c["attrs"])
    my_oc = model.oc(c, w)

    def roll():
        return open_d6() if exploding else [d(6)]

    def note(text, color):
        log.insert(0, {"t": text, "c": color})
        del log[8:]

    def my_attack(e):
        a, dd = roll(), roll()
        at, de = uc + sum(a), foe["oc"] + sum(dd)
        wound = r.wound(at, de, int(w.get("damage", 0)))
        if wound:
            foe["hp"] = foe["hp"] - wound
            note(f"Útok {at} ({uc}+{roll_expr(a)}) proti obraně {de} ({foe['oc']}+{roll_expr(dd)}) – zásah za {wound}",
                 l.accent)
            if foe["hp"] <= 0:
                note(f"{foe['name']} padl!", l.ok)
        else:
            note(f"Útok {at} proti obraně {de} – vedle", l.mana)
        app.ui["round"] += 1
        app.refresh()

    def foe_attack(e):
        a, dd = roll(), roll()
        at, de = foe["uc"] + sum(a), my_oc + sum(dd)
        wound = r.wound(at, de, foe["dmg"])
        if wound:
            c["hp"] -= wound
            model.add_history(c, f"Zranění od: {foe['name']}", f"−{wound}")
            app.save(c)
            note(f"{foe['name']}: útok {at} proti tvé obraně {de} – zranění {wound}", l.bad)
        else:
            note(f"{foe['name']}: útok {at} proti tvé obraně {de} – ubránil ses", l.ok)
        app.refresh()

    def initiative(e):
        if is_dh:
            kk, mine = dh.initiative(dh.bonus(c["attrs"][1]))
            theirs = d(6)
            note(f"Iniciativa: ty {mine} (k6 {kk} {fmt(dh.bonus(c['attrs'][1]))} OBR), soupeř {theirs}", l.ink)
        else:
            mine, theirs = d(6), d(6)
            note(f"Iniciativa: ty {mine}, soupeř {theirs}" + (" – začínáš" if mine > theirs else
                                                              " – začíná soupeř" if theirs > mine else " – znovu"), l.ink)
        app.refresh()

    def edit_foe(e):
        names = ["(vlastní)"] + [b["name"] for b in app.bestiary.get(c["system"], [])]

        def save(v):
            if v["pick"] and v["pick"] != "(vlastní)":
                b = next(b for b in app.bestiary[c["system"]] if b["name"] == v["pick"])
                nf = foe_from_beast(b)
            else:
                nf = {"name": v["name"] or "Soupeř", "uc": v["uc"], "oc": v["oc"], "hp": v["hp"], "hp_max": v["hp"],
                      "dmg": v["dmg"]}
            nf["sys"] = c["system"]
            app.ui["foe"] = nf
            app.ui["fight_log"] = []
            app.ui["round"] = 1
            app.refresh()
        app.form("Soupeř", [("pick", "Z bestiáře", "(vlastní)", "choice", names),
                            ("name", "Jméno", foe["name"], "text"), ("uc", "ÚČ", foe["uc"], "int"),
                            ("oc", "OČ", foe["oc"], "int"), ("hp", "Životy", foe["hp_max"], "int"),
                            ("dmg", "Zranění zbraně / útočnost", foe["dmg"], "int")], save, save_label="Nastavit")

    me_card = k.card(ft.Column([
        k.muted("TY", size=11, weight=ft.FontWeight.BOLD),
        k.text(c["name"].split()[0], size=16, weight=ft.FontWeight.BOLD, max_lines=1),
        k.muted(w["name"], max_lines=1),
        k.text(f"ÚČ {uc} · OČ {my_oc}", size=17, weight=ft.FontWeight.BOLD, head=True, color=l.accent),
        k.bar(c["hp"], c["hp_max"], l.hp), k.muted(f"Životy {c['hp']} / {c['hp_max']}"),
    ], spacing=3), padding=12)
    foe_card = k.card(ft.Column([
        k.muted("SOUPEŘ", size=11, weight=ft.FontWeight.BOLD),
        k.text(foe["name"], size=16, weight=ft.FontWeight.BOLD, max_lines=1),
        k.muted(f"zranění {fmt(foe['dmg'])}"),
        k.text(f"ÚČ {foe['uc']} · OČ {foe['oc']}", size=17, weight=ft.FontWeight.BOLD, head=True, color=l.mana),
        k.bar(max(0, foe["hp"]), foe["hp_max"], l.hp), k.muted(f"Životy {foe['hp']} / {foe['hp_max']}"),
    ], spacing=3), padding=12, on_click=edit_foe)

    weapon_pills = k.pills([x["name"] for x in ws], w["name"],
                           lambda v: app.go("souboj", dice_weapon=[x["name"] for x in ws].index(v)))
    log_rows = [k.text(x["t"], size=13, color=x["c"]) for x in log] or [k.muted("Zatím žádné hody.")]
    controls = [
        ft.Row([ft.Container(me_card, expand=1), ft.Container(foe_card, expand=1)], spacing=8,
               vertical_alignment=ft.CrossAxisAlignment.START),
        k.muted("Klepnutím na soupeře ho změníš nebo vybereš z bestiáře.", size=12),
        weapon_pills,
        ft.Row([k.button("Útočím", my_attack, expand=1), k.button("Soupeř útočí", foe_attack, primary=False, expand=1)],
               spacing=8),
        ft.Row([k.button("Iniciativa", initiative, primary=False, expand=1),
                k.button("Nový boj", lambda e: (app.ui.update({"foe": None}), app.refresh()), primary=False, expand=1)],
               spacing=8),
        k.section(f"Průběh · kolo {app.ui.get('round', 1)}"),
        k.card(ft.Column(log_rows, spacing=6)),
        k.muted(("Útok ÚČ + k6, obrana OČ + k6" + (" (šestka se hází znovu)" if exploding else "") +
                 ". Zranění = rozdíl + zranění zbraně.") if is_dh else
                "Útok ÚČ + k6+, obrana OČ + k6+. Zranění = rozdíl + útočnost zbraně (nejméně 1)."),
    ]
    return Screen("Souboj", [column(controls)])
