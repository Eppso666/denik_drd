"""Batoh: naložení (automaticky nebo ručně), peníze a předměty."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules.common import fmt
from . import catalog
from .kit import column

CATEGORIES = ["Zbraň", "Zbroj", "Štít", "Lektvar", "Surovina", "Ostatní"]
FILTERS = {"Vše": None, "Výzbroj": {"Zbraň", "Zbroj", "Štít"}, "Lektvary": {"Lektvar"}, "Suroviny": {"Surovina"},
           "Ostatní": {"Ostatní"}}


def num(v: float) -> str:
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def batoh(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    unit = "lb" if is_dh else "kg"
    load = model.load(c)
    cap = float(c.get("capacity", 30))
    state, color_key = model.load_state(c)
    color = {"ok": l.ok, "warn": l.warn, "bad": l.bad}[color_key]

    def set_mode(v):
        c["load_manual"] = v == "Ručně"
        if c["load_manual"] and not c.get("load_value"):
            c["load_value"] = model.items_weight(c)
        app.save(c)
        app.refresh()

    def adj(key, delta, lo):
        def h(e):
            c[key] = max(lo, round(float(c.get(key, 0)) + delta, 1))
            app.save(c)
            app.refresh()
        return h

    load_rows: list[ft.Control] = [
        ft.Row([k.text("Naložení", size=16, weight=ft.FontWeight.BOLD),
                k.pills(["Z předmětů", "Ručně"], "Ručně" if c.get("load_manual") else "Z předmětů", set_mode,
                        wrap=False)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Row([k.text(f"{num(load)} / {num(cap)} {unit}", size=22, weight=ft.FontWeight.BOLD, head=True),
                k.text(state, size=14, weight=ft.FontWeight.BOLD, color=color)],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        k.bar(load, cap, color),
    ]
    if c.get("load_manual"):
        load_rows.append(k.stepper(num(load), adj("load_value", -0.5, 0), adj("load_value", +0.5, 0),
                                   label=f"Nesená váha ({unit})", sub=f"po 0,5 {unit}"))
    rule_cap = model.default_capacity(c)
    load_rows.append(k.stepper(num(cap), adj("capacity", -1, 1), adj("capacity", +1, 1), label=f"Nosnost ({unit})",
                               sub=f"podle pravidel {num(rule_cap)} {unit}" + (
                                   f" ({int(round(rule_cap * 20))} mn)" if not is_dh else "")))
    if abs(cap - rule_cap) > 0.01:
        def set_rule_cap(e):
            c["capacity"] = rule_cap
            app.save(c)
            app.refresh()
        load_rows.append(ft.TextButton(f"Nastavit nosnost podle pravidel ({num(rule_cap)} {unit})",
                                       on_click=set_rule_cap))

    m = c["money"]

    def edit_money(e):
        def save(v):
            c["money"] = {"zl": max(0, v["zl"]), "st": max(0, v["st"]), "md": max(0, v["md"])}
            app.save(c)
            app.refresh()
        app.form("Peníze", [("zl", "Zlaťáky", m["zl"], "int"), ("st", "Stříbrňáky", m["st"], "int"),
                            ("md", "Měďáky", m["md"], "int")], save)

    money = ft.Row([k.stat("ZLATÉ", m["zl"], on_click=edit_money), k.stat("STŘÍBRNÉ", m["st"], on_click=edit_money),
                    k.stat("MĚDĚNÉ", m["md"], on_click=edit_money)], spacing=6)

    flt = app.ui.get("bag_filter", "Vše")
    allowed = FILTERS.get(flt)
    items = [i for i in c["items"] if allowed is None or i["category"] in allowed]
    worn = [i for i in items if i.get("equipped")]
    packed = [i for i in items if not i.get("equipped")]

    def item_row(i: dict) -> ft.Control:
        sub = i["category"]
        if i["category"] == "Zbraň":
            sub += (f" · útočnost {i.get('attack', 0)} · zranění {fmt(int(i.get('damage', 0)))} · obrana {i.get('defense', 0)}"
                    if is_dh else f" · SZ {i.get('attack', 0)} · Út {fmt(int(i.get('damage', 0)))} · OZ {i.get('defense', 0)}")
            if i.get("ranged"):
                sub += " · střelná"
        elif i["category"] == "Zbroj":
            sub += f" · kvalita {i.get('quality', 0)}"
        if i.get("price"):
            sub += f" · {i['price']}"
        elif i["category"] == "Štít":
            sub += f" · obrana {fmt(int(i.get('defense', 1)))}"
        right = f"{num(float(i.get('weight', 0)) * int(i.get('qty', 1)))} {unit}"
        qty = f"×{i.get('qty', 1)}"
        return k.row_item(i["name"], right, sub=sub, badge=qty if int(i.get("qty", 1)) > 1 else None,
                          on_click=lambda e, i=i: edit_item(app, i))

    controls: list[ft.Control] = [
        k.card(ft.Column(load_rows, spacing=10)),
        money,
        k.pills(list(FILTERS), flt, lambda v: app.go("batoh", bag_filter=v)),
        k.section("Vybaveno na těle"),
        k.list_card([item_row(i) for i in worn]) if worn else k.empty("Nic vybaveného."),
        k.section("V batohu"),
        k.list_card([item_row(i) for i in packed]) if packed else k.empty("Batoh je prázdný."),
        ft.Container(height=70),
    ]
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=l.accent, foreground_color=l.on_accent,
                                  tooltip="Přidat předmět", on_click=lambda e: catalog.open_add_menu(app))
    return Screen("Batoh", [column(controls)], fab=fab)


def edit_item(app, i: dict | None) -> None:
    c = app.char
    is_dh = c["system"] == "dh"
    g = (lambda key, default=0: i.get(key, default) if i else default)
    fields = [
        ("name", "Název", g("name", ""), "text"),
        ("category", "Druh", g("category", "Ostatní"), "choice", CATEGORIES),
        ("qty", "Počet kusů", g("qty", 1), "int"),
        ("weight", f"Váha jednoho kusu ({'lb' if is_dh else 'kg'})", g("weight", 0), "float"),
        ("equipped", "Vybaveno na těle (počítá se do boje)", g("equipped", False), "bool"),
        ("attack", "Zbraň: útočnost" if is_dh else "Zbraň: síla zbraně (SZ)", g("attack", 0), "int"),
        ("damage", "Zbraň: zranění" if is_dh else "Zbraň: útočnost (Út)", g("damage", 0), "int"),
        ("defense", "Zbraň: obrana / Štít: bonus k obraně" if is_dh else "Zbraň: obrana (OZ) / Štít: bonus",
         g("defense", 0), "int"),
        ("ranged", "Střelná zbraň", g("ranged", False), "bool"),
        ("quality", "Zbroj: kvalita", g("quality", 0), "int"),
    ]
    if i is None:
        fields.append(("save_tpl", "Uložit i do „Moje předměty“ (pro další postavy)", False, "bool"))

    def save(v):
        if not v["name"].strip():
            app.toast("Vyplň název předmětu.")
            return
        v["name"] = v["name"].strip()
        v["category"] = v["category"] or "Ostatní"
        v["qty"] = max(1, int(v["qty"]))
        v["weight"] = max(0.0, float(v["weight"]))
        tpl = v.pop("save_tpl", False)
        if i is None:
            c["items"].append(model.item(**v))
            if tpl:
                catalog.save_template(app, c["system"], v)
        else:
            i.update(v)
        app.save(c)
        app.refresh()

    def delete():
        c["items"].remove(i)
        app.save(c)
        app.refresh()

    app.form("Nový předmět" if i is None else "Upravit předmět", fields, save,
             on_delete=delete if i is not None else None)
