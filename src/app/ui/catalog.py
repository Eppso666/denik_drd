"""Batoh: výběr výzbroje a výstroje z pravidel a vlastní šablony předmětů."""
from __future__ import annotations

import re

import flet as ft

from .. import model
from ..rules import dh, dh_vybava, drd_vybava
from ..rules.common import fmt
from .kit import column, matches

MINE = "Moje předměty"
ITEM_KEYS = ("name", "category", "weight", "attack", "damage", "defense", "ranged", "quality", "price", "info",
             "range", "hands", "sil_req")


def rules_catalog(c: dict) -> list[dict]:
    if c["system"] == "dh":
        return dh_vybava.catalog(c.get("race"))
    return drd_vybava.catalog(c.get("race"))


def custom_templates(app, system: str) -> list[dict]:
    return app.settings.setdefault("custom_items", {}).setdefault(system, [])


def price_md(price: str) -> int | None:
    """„1 zl 5 st“ → měďáky (1 zl = 10 st = 100 md). Neznámá cena → None."""
    if not price or not re.search(r"\d", price):
        return None
    total = 0
    for num, unit in re.findall(r"(\d+)\s*(zl|st|md)", price):
        total += int(num) * {"zl": 100, "st": 10, "md": 1}[unit]
    return total if total or "0" in price else None


def money_md(m: dict) -> int:
    return int(m.get("zl", 0)) * 100 + int(m.get("st", 0)) * 10 + int(m.get("md", 0))


def pay(c: dict, cost: int) -> bool:
    m = c["money"]
    have = money_md(m)
    if have < cost:
        return False
    rest = have - cost
    c["money"] = {"zl": rest // 100, "st": (rest % 100) // 10, "md": rest % 10}
    return True


def weight_label(c: dict, it: dict) -> str:
    if c["system"] == "drd" and it.get("weight_mn") is not None:
        return f"{it['weight_mn']} mn"
    w = float(it.get("weight", 0))
    return f"{w:g} lb".replace(".", ",") if c["system"] == "dh" else f"{w:g} kg".replace(".", ",")


def stats_label(c: dict, it: dict) -> str:
    is_dh = c["system"] == "dh"
    if it["category"] == "Zbraň":
        if is_dh:
            return f"útočnost {it.get('attack', 0)} · zranění {it.get('damage', 0)} · obrana {it.get('defense', 0)}"
        return f"SZ {it.get('attack', 0)} · Út {fmt(int(it.get('damage', 0)))} · OZ {fmt(int(it.get('defense', 0)))}"
    if it["category"] == "Zbroj":
        return f"{'kvalita' if is_dh else 'KZ'} {it.get('quality', 0)}"
    if it["category"] == "Štít":
        return f"obrana +{it.get('defense', 1)}"
    return ""


def open_add_menu(app) -> None:
    """FAB v batohu: z pravidel, nebo vlastní předmět."""
    from .inventory import edit_item
    k = app.kit
    l = app.look

    def rules(e):
        app.close_dialog()
        app.go("katalog")

    def own(e):
        app.close_dialog()
        edit_item(app, None)

    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Přidat předmět", size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column([
            k.button("Z pravidel (zbraně, zbroje, výstroj)", rules, icon=ft.Icons.MENU_BOOK_OUTLINED),
            k.button("Vlastní předmět", own, primary=False, icon=ft.Icons.EDIT_OUTLINED),
        ], spacing=10, tight=True), width=340),
        actions=[ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog())],
    ))


def katalog(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    items = rules_catalog(c)
    groups = list(dict.fromkeys(i["group"] for i in items)) + [MINE]
    grp = app.ui.get("cat_group") or groups[0]
    if grp not in groups:
        grp = groups[0]
    q = app.ui.get("cat_q", "")
    if q:
        mine = [dict(t, group=MINE) for t in custom_templates(app, c["system"])]
        shown = [i for i in items + mine if matches(q, i["name"], i.get("info"), i["group"])]
    elif grp == MINE:
        shown = [dict(t, group=MINE) for t in custom_templates(app, c["system"])]
    else:
        shown = [i for i in items if i["group"] == grp]

    rows = []
    for it in shown:
        sub = " · ".join(x for x in (stats_label(c, it), it.get("info", "")) if x)
        right = " · ".join(x for x in (it.get("price") or "", weight_label(c, it)) if x)
        if q:
            sub = " · ".join(x for x in (it["group"], sub) if x)
        rows.append(k.row_item(it["name"], right, sub=sub, on_click=lambda e, it=it: item_dialog(app, it)))
    size = (dh_vybava.RACE_SIZE if c["system"] == "dh" else drd_vybava.RACE_SIZE).get(c["race"], "B")
    note = ("Ceny jsou podle pravidel jen orientační. Zbroje jsou pro velikost "
            f"{size} ({c['race']}).")
    if c["system"] == "drd":
        note += " Váha v mincích (20 mn ≈ 1 kg). Střelné a vrhací zbraně mají OZ −2."
    else:
        note += " Hmotnost v librách (1 lb ≈ 1 kg). Těžší zbraně a zbroje vyžadují opravu za Sílu."
    controls = [
        k.search(q, lambda v: app.go("katalog", cat_q=v), "Hledat ve všech skupinách…"),
    ]
    if not q:
        controls.append(k.pills(groups, grp, lambda v: app.go("katalog", cat_group=v, cat_q="")))
    controls += [
        k.list_card(rows) if rows else k.empty(
            f"Nic neodpovídá hledání „{q}“." if q else
            "Zatím žádné vlastní šablony. Ulož si je při vytváření vlastního předmětu."
            if grp == MINE else "Prázdné."),
        k.muted(note, size=12),
    ]
    return Screen("Z pravidel", [column(controls)])


def item_dialog(app, it: dict) -> None:
    c = app.char
    k = app.kit
    l = app.look
    cost = price_md(it.get("price", ""))
    qty_field = ft.TextField(label="Počet kusů", value="1", keyboard_type=ft.KeyboardType.NUMBER,
                             border_color=l.frame, focused_border_color=l.hi, color=l.ink, width=140)
    equip = ft.Switch(label="Vybavit na tělo (počítá se do boje)",
                      value=it["category"] in ("Zbraň", "Zbroj", "Štít"), active_color=l.hi)

    def qty() -> int:
        try:
            return max(1, int(qty_field.value or 1))
        except ValueError:
            return 1

    def add(buy: bool):
        def h(e):
            n = qty()
            if buy and cost is not None:
                if not pay(c, cost * n):
                    app.toast("Na to nemáš dost peněz.")
                    return
            data = {key: it[key] for key in ITEM_KEYS if key in it and key not in ("name", "category", "weight")}
            new = model.item(it["name"], it["category"], qty=n, weight=float(it.get("weight", 0)),
                             equipped=bool(equip.value), **data)
            c["items"].append(new)
            model.add_history(c, "Koupeno" if buy else "Přidáno", f"{n}× {it['name']}")
            app.save(c)
            app.close_dialog()
            app.toast(f"{it['name']} je v batohu" + (f" (−{it['price']})" if buy and cost else "") + ".")
            app.go("batoh")
        return h

    def remove_template(e):
        lst = custom_templates(app, c["system"])
        for t in list(lst):
            if t.get("name") == it["name"]:
                lst.remove(t)
        app.save(settings=True)
        app.close_dialog()
        app.refresh()

    body: list[ft.Control] = []
    st = stats_label(c, it)
    if st:
        body.append(k.text(st, size=15, weight=ft.FontWeight.W_600))
    if it.get("info"):
        body.append(k.muted(it["info"], size=13))
    body.append(k.muted(" · ".join(x for x in (f"cena {it['price']}" if it.get("price") else "",
                                               f"váha {weight_label(c, it)}") if x), size=13))
    if c["system"] == "drd":
        prob = drd_vybava.gear_problem(c["cls"], it)
    else:
        req = it.get("sil_req")
        sil = dh.bonus(c["attrs"][0])
        prob = (f"Potřebuje Sílu {'+' if req > 0 else ''}{req}, máš {sil:+d} – při nošení dostaneš body únavy navíc."
                if req is not None and sil < int(req) else None)
    if prob:
        body.append(k.text(prob, size=13, color=l.warn))
    if int(it.get("hands", 1)) >= 2 and it["category"] == "Zbraň":
        body.append(k.muted("Drží se oběma rukama – štít s ní nelze použít.", size=12))
    body += [qty_field, equip]
    actions: list[ft.Control] = []
    if it.get("group") == MINE:
        actions.append(ft.TextButton("Smazat šablonu", on_click=remove_template, style=ft.ButtonStyle(color=l.bad)))
    actions.append(ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()))
    if cost:
        actions.append(ft.TextButton("Koupit", on_click=add(True)))
    actions.append(ft.FilledButton(content=ft.Text("Přidat"), on_click=add(False),
                                   style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent)))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(it["name"], size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column(body, spacing=10, tight=True), width=360), actions=actions,
    ))


def save_template(app, system: str, it: dict) -> None:
    lst = custom_templates(app, system)
    tpl = {key: it[key] for key in ITEM_KEYS if key in it}
    tpl["info"] = tpl.get("info") or "vlastní předmět"
    lst[:] = [t for t in lst if t.get("name") != tpl["name"]] + [tpl]
    app.save(settings=True)
