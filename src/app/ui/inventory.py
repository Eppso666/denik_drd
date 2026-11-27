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

    def change(how: str):
        def h(e):
            from .catalog import exchange
            new = exchange(c["money"], how)
            if new is None:
                app.toast("Není co měnit.")
                return
            c["money"] = new
            app.save(c)
            app.refresh()
        return h

    coins = ft.Row([k.stat("ZLATÉ", m["zl"], on_click=edit_money), k.stat("STŘÍBRNÉ", m["st"], on_click=edit_money),
                    k.stat("MĚDĚNÉ", m["md"], on_click=edit_money)], spacing=6)
    if is_dh:
        money = coins
    else:
        from .catalog import fmt_md, money_md
        total = money_md(m)
        money = ft.Column([
            coins,
            ft.Row([ft.TextButton("Rozměnit 1 zl", on_click=change("zl")),
                    ft.TextButton("Rozměnit 1 st", on_click=change("st")),
                    ft.TextButton("Sloučit drobné", on_click=change("sloucit"))], wrap=True, spacing=0),
            k.muted(f"1 zl = 10 st = 100 md · celkem {total / 100:.2f} zl".replace(".", ",")
                    + (f" ({fmt_md(total)})" if total % 100 else ""), size=12),
        ], spacing=2)

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
            sub += f" · obrana {fmt(model.shield_value(c, i))}"
        right = f"{num(float(i.get('weight', 0)) * int(i.get('qty', 1)))} {unit}"
        qty = f"×{i.get('qty', 1)}"
        return k.row_item(i["name"], right, sub=sub, badge=qty if int(i.get("qty", 1)) > 1 else None,
                          note=(i.get("desc") or "").strip().replace("\n", " ") or None,
                          on_click=lambda e, i=i: item_detail(app, i))

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


def item_detail(app, i: dict) -> None:
    """Detail předmětu podle návrhu: popis na pergamenu, údaje, Sundat/Vybavit a Upravit."""
    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    unit = "lb" if is_dh else "kg"
    icon = {"Zbraň": ft.Icons.SPORTS_MARTIAL_ARTS, "Zbroj": ft.Icons.SHIELD_OUTLINED,
            "Štít": ft.Icons.SHIELD_OUTLINED}.get(i["category"], ft.Icons.BACKPACK_OUTLINED)
    head: list[ft.Control] = [ft.Icon(icon, size=22, color=l.orn),
                              k.text(i["name"], size=20, weight=ft.FontWeight.BOLD, head=True, expand=True, max_lines=2)]
    if i.get("equipped"):
        head.append(k.badge("NA TĚLE"))
    rows = [("Druh", i["category"])]
    if i["category"] == "Zbraň":
        rows.append(("Útočnost · zranění · obrana" if is_dh else "SZ · útočnost · OZ",
                     f"{i.get('attack', 0)} · {fmt(int(i.get('damage', 0)))} · {i.get('defense', 0)}"
                     + (" · střelná" if i.get("ranged") else "")))
    elif i["category"] == "Zbroj":
        rows.append(("Kvalita", str(i.get("quality", 0))))
    elif i["category"] == "Štít":
        rows.append(("Bonus k obraně", fmt(model.shield_value(app.char, i))))
    rows.append(("Počet · váha", f"{i.get('qty', 1)} · {num(float(i.get('weight', 0)))} {unit}"))
    desc = (i.get("desc") or "").strip()

    def toggle(e):
        i["equipped"] = not i.get("equipped")
        app.close_dialog()
        app.save(c)
        app.refresh()

    def edit(e):
        app.close_dialog()
        edit_item(app, i)

    body: list[ft.Control] = [
        ft.Row(head, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        k.divider(),
        k.text("POPIS", size=11, weight=ft.FontWeight.BOLD, color=l.muted),
        k.parch(k.text(desc, size=15, color=l.ptext)) if desc else
        k.muted("Bez popisu – doplníš ho v Upravit.", size=13),
        *[ft.Container(ft.Row([k.muted(a, size=14, expand=True), k.text(b, size=14, weight=ft.FontWeight.BOLD)]),
                       padding=ft.Padding.symmetric(vertical=5),
                       border=ft.Border.only(bottom=ft.BorderSide(1, l.border))) for a, b in rows],
        ft.Row([k.button("Sundat" if i.get("equipped") else "Vybavit", toggle, primary=False,
                         icon=ft.Icons.SHIELD_OUTLINED, expand=1, height=44),
                k.button("Upravit", edit, icon=ft.Icons.EDIT_OUTLINED, expand=1, height=44)], spacing=8),
    ]
    app.page.show_dialog(ft.AlertDialog(
        content=ft.Container(ft.Column(body, spacing=10, tight=True), width=360), bgcolor=l.card))


def edit_item(app, i: dict | None) -> None:
    """Formulář předmětu podle návrhu: Název, Popis, Druh, počet a váha vedle sebe, údaje podle druhu."""
    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    g = (lambda key, default=0: i.get(key, default) if i else default)

    def tf(label, value, number=False, multiline=False):
        return ft.TextField(label=label, value="" if value is None else str(value), multiline=multiline,
                            min_lines=3 if multiline else None, max_lines=8 if multiline else 1,
                            keyboard_type=ft.KeyboardType.NUMBER if number else ft.KeyboardType.TEXT,
                            border_color=l.frame, focused_border_color=l.hi, color=l.ink, cursor_color=l.hi,
                            expand=True)
    f = {
        "name": tf("Název", g("name", "")),
        "desc": tf("Popis", g("desc", ""), multiline=True),
        "category": ft.Dropdown(label="Druh", value=g("category", "Ostatní"),
                                options=[ft.DropdownOption(key=o, text=o) for o in CATEGORIES], expand=True,
                                border_color=l.frame, focused_border_color=l.hi, color=l.ink),
        "qty": tf("Počet kusů", g("qty", 1), True),
        "weight": tf(f"Váha jednoho kusu ({'lb' if is_dh else 'kg'})", g("weight", 0), True),
        "equipped": ft.Switch(label="Vybaveno na těle (počítá se do boje)", value=bool(g("equipped", False)),
                              active_color=l.hi),
        "attack": tf("Útočnost" if is_dh else "SZ", g("attack", 0), True),
        "damage": tf("Zranění" if is_dh else "Útočnost", g("damage", 0), True),
        "defense": tf("Obrana" if is_dh else "OZ", g("defense", 0), True),
        "ranged": ft.Switch(label="Střelná zbraň", value=bool(g("ranged", False)), active_color=l.hi),
        "shield": tf("Bonus k obraně", g("defense", 1), True),
        "quality": tf("Kvalita zbroje", g("quality", 0), True),
        "save_tpl": ft.Switch(label="Uložit i do „Moje předměty“ (pro další postavy)", value=False, active_color=l.hi),
    }
    holder = ft.Column(spacing=12, tight=True)

    def draw(e=None):
        cat = f["category"].value or "Ostatní"
        rows: list[ft.Control] = [f["name"], f["desc"],
                                  k.muted("Vlastní poznámka k předmětu: odkud je, co umí, komu patřil. "
                                          "Ukáže se v batohu i v detailu.", size=12),
                                  f["category"], ft.Row([f["qty"], f["weight"]], spacing=10), f["equipped"]]
        if cat == "Zbraň":
            rows += [ft.Row([f["attack"], f["damage"], f["defense"]], spacing=8), f["ranged"]]
        elif cat == "Štít":
            rows.append(f["shield"] if is_dh else k.muted("Štít dává k hodu na obranu vždy +1 (pravidla DrD).",
                                                          size=12))
        elif cat == "Zbroj":
            rows.append(f["quality"])
        if i is None:
            rows.append(f["save_tpl"])
        holder.controls = rows
        if e is not None:
            try:
                app.page.update()
            except Exception:
                pass
    f["category"].on_select = draw
    draw()

    def number(key, cast=int, default=0):
        try:
            return cast(str(f[key].value).replace(",", ".") or default) if cast is float else \
                int(float(str(f[key].value).replace(",", ".") or default))
        except ValueError:
            return default

    def save(e):
        name = (f["name"].value or "").strip()
        if not name:
            app.toast("Vyplň název předmětu.")
            return
        cat = f["category"].value or "Ostatní"
        v = {"name": name, "desc": (f["desc"].value or "").strip(), "category": cat,
             "qty": max(1, number("qty", int, 1)), "weight": max(0.0, number("weight", float, 0.0)),
             "equipped": bool(f["equipped"].value),
             "attack": number("attack"), "damage": number("damage"),
             "defense": number("shield", int, 1) if cat == "Štít" else number("defense"),
             "ranged": bool(f["ranged"].value) if cat == "Zbraň" else False, "quality": number("quality")}
        app.close_dialog()
        if i is None:
            c["items"].append(model.item(**v))
            if f["save_tpl"].value:
                catalog.save_template(app, c["system"], v)
        else:
            i.update(v)
        app.save(c)
        app.refresh()

    def delete(e):
        app.close_dialog()

        async def do():
            c["items"].remove(i)
            app.save(c)
            app.refresh()
        app.confirm("Opravdu smazat?", "Tuto akci nejde vrátit.", do)

    actions: list[ft.Control] = []
    if i is not None:
        actions.append(ft.TextButton("Smazat", on_click=delete, style=ft.ButtonStyle(color=l.bad)))
    actions += [ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()),
                ft.FilledButton(content=ft.Row([ft.Icon(ft.Icons.CHECK, size=18), ft.Text("Uložit")], tight=True,
                                               spacing=6),
                                on_click=save, style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))]
    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Nový předmět" if i is None else "Upravit předmět", size=19, weight=ft.FontWeight.BOLD, head=True),
        bgcolor=l.card, content=ft.Container(ft.Column([holder], tight=True, scroll=ft.ScrollMode.AUTO), width=360),
        actions=actions))
