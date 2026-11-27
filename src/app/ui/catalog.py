"""Batoh: výběr výzbroje a výstroje z pravidel a vlastní šablony předmětů."""
from __future__ import annotations

import re

import flet as ft

from .. import model
from ..rules import dh, dh_vybava, drd_vybava
from ..rules.common import fmt
from .kit import column, matches

MINE = "Moje předměty"
ITEM_KEYS = ("desc", "name", "category", "weight", "attack", "damage", "defense", "ranged", "quality", "price", "info",
             "range", "hands", "sil_req")


def rules_catalog(c: dict) -> list[dict]:
    if c["system"] == "dh":
        return dh_vybava.catalog(c.get("race"))
    return drd_vybava.catalog(c.get("race"))


def custom_templates(app, system: str) -> list[dict]:
    return app.settings.setdefault("custom_items", {}).setdefault(system, [])


def _amount_md(text: str, unit: str | None = None) -> int | None:
    found = re.findall(r"(\d+)\s*(zl|st|md)?", text.replace("\u00a0", " "))
    if not found:
        return None
    total = 0
    for num, u in found:
        u = u or unit
        if not u:
            return None
        total += int(num) * {"zl": 100, "st": 10, "md": 1}[u]
    return total


def price_range(price: str) -> tuple[int, int] | None:
    """Cena z ceníku → (od, do) v měďácích. „5 st až 3 zl“, „1–3 zl“, „1 zl 5 st“; „?“ nebo prázdná → None."""
    if not price or "?" in price or not re.search(r"\d", price):
        return None
    parts = [x.strip() for x in re.split(r"\s*(?:až|–|-)\s*", price) if x.strip()]
    if len(parts) == 2:
        unit = re.findall(r"(zl|st|md)", parts[1])
        lo = _amount_md(parts[0], unit[-1] if unit else None)
        hi = _amount_md(parts[1])
        if lo is None or hi is None:
            return None
        return (min(lo, hi), max(lo, hi))
    v = _amount_md(price)
    return None if v is None else (v, v)


def price_md(price: str) -> int | None:
    """Pevná cena „1 zl 5 st“ → měďáky (1 zl = 10 st = 100 md). Rozpětí nebo neznámá cena → None."""
    r = price_range(price)
    return r[0] if r and r[0] == r[1] else None


def fmt_md(v: int) -> str:
    """Měďáky → „1 zl 5 st 2 md“."""
    v = max(0, int(v))
    parts = [f"{n} {u}" for n, u in ((v // 100, "zl"), ((v % 100) // 10, "st"), (v % 10, "md")) if n]
    return " ".join(parts) or "0 md"


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


def exchange(m: dict, how: str) -> dict | None:
    """Směna mincí (1 zl = 10 st = 100 md). how: „sloucit“ (drobné nahoru), „zl“ (1 zl → 10 st), „st“ (1 st → 10 md).
    Vrací nové peníze, nebo None, když není co měnit."""
    zl, st, md = int(m.get("zl", 0)), int(m.get("st", 0)), int(m.get("md", 0))
    if how == "sloucit":
        if md < 10 and st < 10:
            return None
        st, md = st + md // 10, md % 10
        zl, st = zl + st // 10, st % 10
    elif how == "zl":
        if zl < 1:
            return None
        zl, st = zl - 1, st + 10
    elif how == "st":
        if st < 1:
            return None
        st, md = st - 1, md + 10
    return {"zl": zl, "st": st, "md": md}


def weight_label(c: dict, it: dict) -> str:
    if c["system"] == "drd" and it.get("weight_mn") is not None:
        return f"{it['weight_mn']:g} mn".replace(".", ",")
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
    rng = price_range(it.get("price", ""))
    qty_field = ft.TextField(label="Počet kusů", value="1", keyboard_type=ft.KeyboardType.NUMBER,
                             border_color=l.frame, focused_border_color=l.hi, color=l.ink, width=110)
    price_field = ft.TextField(label="Cena za kus", value=fmt_md(rng[0]) if rng else "",
                               hint_text="např. 2 zl 5 st", border_color=l.frame, focused_border_color=l.hi,
                               color=l.ink, expand=True)
    equip = ft.Switch(label="Vybavit na tělo (počítá se do boje)",
                      value=it["category"] in ("Zbraň", "Zbroj", "Štít"), active_color=l.hi)
    total_txt = k.muted("", size=13)
    buy_btn = ft.TextButton("Koupit")
    state = {"armed": False}

    def qty() -> int:
        try:
            return max(1, int(qty_field.value or 1))
        except ValueError:
            return 1

    def total() -> int | None:
        unit = price_md(price_field.value or "")
        return None if unit is None else unit * qty()

    def _upd(*ctrls):
        for x in ctrls:
            try:
                x.update()
            except Exception:  # noqa: BLE001 – ovládací prvek ještě není na stránce
                pass

    def refresh_total(e=None):
        t = total()
        have = money_md(c["money"])
        if t is None:
            total_txt.value = f"Máš {fmt_md(have)}." + (" Cenu určí PJ – zapiš ji pro nákup." if not rng else "")
        else:
            total_txt.value = (f"Celkem {fmt_md(t)} · máš {fmt_md(have)}"
                               + (f" · zbyde {fmt_md(have - t)}" if have >= t else " · nestačí"))
        state["armed"] = False
        buy_btn.content = "Koupit"
        _upd(total_txt, buy_btn)

    qty_field.on_change = refresh_total
    price_field.on_change = refresh_total
    refresh_total()

    def put_in_bag(n: int, bought: str | None):
        data = {key: it[key] for key in ITEM_KEYS if key in it and key not in ("name", "category", "weight")}
        new = model.item(it["name"], it["category"], qty=n, weight=float(it.get("weight", 0)),
                         equipped=bool(equip.value), **data)
        c["items"].append(new)
        model.add_history(c, "Koupeno" if bought else "Přidáno",
                          f"{n}× {it['name']}" + (f" za {bought}" if bought else ""))
        app.save(c)
        app.close_dialog()
        app.toast(f"{it['name']} je v batohu" + (f" (−{bought})" if bought else "") + ".")
        app.go("batoh")

    def add(e):
        put_in_bag(qty(), None)

    def buy(e):
        t = total()
        if t is None:
            app.toast("Zapiš cenu za kus, např. „2 zl 5 st“.")
            return
        if money_md(c["money"]) < t:
            app.toast(f"Na to nemáš dost peněz (chybí {fmt_md(t - money_md(c['money']))}).")
            return
        if not state["armed"]:  # potvrzení druhým klepnutím
            state["armed"] = True
            buy_btn.content = f"Zaplatit {fmt_md(t)}?"
            _upd(buy_btn)
            return
        pay(c, t)
        put_in_bag(qty(), fmt_md(t))

    buy_btn.on_click = buy

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
    if it.get("price") and rng and rng[0] != rng[1]:
        body.append(k.muted("Cena se pohybuje v rozpětí – dohodni ji s PJ a uprav níže.", size=12))
    body += [ft.Row([qty_field, price_field], spacing=8), total_txt, equip]
    actions: list[ft.Control] = []
    if it.get("group") == MINE:
        actions.append(ft.TextButton("Smazat šablonu", on_click=remove_template, style=ft.ButtonStyle(color=l.bad)))
    actions.append(ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()))
    actions.append(buy_btn)
    actions.append(ft.FilledButton(content=ft.Text("Přidat"), on_click=add,
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
