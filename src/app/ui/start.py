"""Společné obrazovky: výběr postavy a generátor postavy."""
from __future__ import annotations

import flet as ft

from .. import model, theme
from ..rules import dh, drd
from ..rules.common import fmt
from .kit import column

SYS = {"dh": dh, "drd": drd}


def start(app):
    from ..core import Screen

    k = app.kit
    l = app.look
    controls: list[ft.Control] = [k.muted("DENÍK DOBRODRUHA", size=12, weight=ft.FontWeight.BOLD, color=l.accent)]

    if not app.order:
        controls.append(k.card(ft.Column([
            ft.Icon(ft.Icons.CASINO_OUTLINED, size=56, color=l.accent),
            k.text("Zatím žádná postava", size=20, weight=ft.FontWeight.BOLD, head=True),
            k.muted("Vytvoř si první postavu. Vybereš, jestli hraješ Dračí Hlídku, nebo Dračí doupě 1.6, "
                    "a aplikace se přizpůsobí pravidlům i vzhledem.", size=14, align=ft.TextAlign.CENTER),
            k.button("Vytvořit postavu", lambda e: open_generator(app), expand=False),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), padding=24))
    else:
        for cid in app.order:
            c = app.chars[cid]
            controls.append(character_card(app, c))
        controls.append(k.button("Nová postava", lambda e: open_generator(app), primary=False, icon=ft.Icons.ADD))

    controls.append(ft.Container(height=8))
    controls.append(k.section("Kampaně a družina"))
    controls.append(k.card(ft.Column([
        k.text("Propojení s ostatními hráči", size=15, weight=ft.FontWeight.W_600),
        k.muted("Sdílené kampaně, hody družiny a mapy od PJ přibudou v další verzi (Supabase). "
                "Tato verze ukládá vše jen v tomto zařízení.", size=13),
    ], spacing=4)))
    return Screen("Tvoje postavy", [column(controls)])


def character_card(app, c: dict) -> ft.Control:
    k = app.kit
    l = app.look
    own = theme.for_system(c["system"])
    r = SYS[c["system"]]
    initials = "".join(p[0] for p in c["name"].split()[:2]).upper() or "?"
    avatar = ft.Container(
        ft.Text(initials, size=20, weight=ft.FontWeight.BOLD, color=own.accent),
        width=56, height=56, alignment=ft.Alignment.CENTER, bgcolor=own.bg if own.key == "drd" else l.card2,
        border=ft.Border.all(2, own.accent), border_radius=ft.BorderRadius.all(14),
    )
    badge = k.badge(r.SHORT, color=own.accent if own.key == "dh" else own.bg,
                    fg=own.on_accent if own.key == "dh" else own.accent)

    def delete(e):
        async def do():
            await app.delete_character(c["id"])
            app.render()
        app.confirm("Smazat postavu?", f"{c['name']} bude smazán i s deníkem a obrázky.", do)

    body = ft.Row([
        avatar,
        ft.Column([
            k.text(c["name"], size=16, weight=ft.FontWeight.BOLD, max_lines=1),
            k.muted(f"{c['race']} · {c['cls']} · {c['level']}. úroveň", max_lines=1),
            k.bar(c["hp"], c["hp_max"], l.hp),
        ], spacing=4, expand=True),
        ft.Column([badge, ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=l.muted, tooltip="Smazat postavu",
                                        on_click=delete)], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return k.card(body, on_click=lambda e: app.open_character(c["id"]))


# --- generátor ---------------------------------------------------------------

def open_generator(app) -> None:
    app.ui.update({"gen_sys": "dh", "gen_mode": "auto", "gen_name": ""})
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
                        border_color=l.border, focused_border_color=l.accent, color=l.ink, cursor_color=l.accent)

    rows: list[ft.Control] = []
    left = 0
    if s == "dh" and manual:
        left = dh.POINT_POOL - sum(u["gen_points"])
    for i, a in enumerate(r.ATTRS):
        val = u["gen_attrs"][i]
        b = r.bonus(val)
        sub = None
        if s == "drd":
            lo, hi = drd.attr_range(u["gen_race"], u["gen_cls"], i)
            n, add = drd.range_dice(lo, hi)
            sub = f"rozsah {lo}–{hi} ({n}k6{fmt(add) if add else ''})"
        elif manual:
            sub = f"body {u['gen_points'][i]} + rodový {dh.RACES[u['gen_race']][i]}" + (
                " + 3" if a in dh.CLASSES[u['gen_cls']] else "")
        else:
            sub = "dominantní +3" if a in dh.CLASSES[u["gen_cls"]] else None
        label = f"{a}  ·  oprava {fmt(b)}"
        if manual:
            rows.append(k.stepper(val, lambda e, i=i: step(app, i, -1), lambda e, i=i: step(app, i, +1),
                                  label=label, sub=sub))
        else:
            rows.append(ft.Row([
                ft.Column([k.text(label, size=15, weight=ft.FontWeight.W_600)] + ([k.muted(sub)] if sub else []),
                          spacing=2, expand=True),
                k.text(val, size=24, weight=ft.FontWeight.BOLD, head=True),
            ]))

    if s == "dh":
        hint = (f"Rozděl {dh.POINT_POOL} bodů (do každé vlastnosti 1–6). Zbývá: {left}." if manual else
                "6× k6, nejnižší hod se škrtá, zbylé se rozdělí. Přičten rodový základ a +3 k dominantním vlastnostem.")
    else:
        hint = ("Zadej hodnoty, které jsi hodil fyzickými kostkami (v povoleném rozsahu)." if manual else
                "Vlastnosti hozeny podle tabulek rasy a povolání.")

    attrs_card = k.card(ft.Column([
        ft.Row([k.text("Vlastnosti", size=17, weight=ft.FontWeight.BOLD, head=True, color=l.accent),
                k.pills(["Automaticky", "Ručně"], "Ručně" if manual else "Automaticky", set_mode, wrap=False)],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        k.muted(hint),
        *rows,
        *([] if manual else [k.button("Hodit znovu", lambda e: (reroll(app), app.refresh()), primary=False,
                                      icon=ft.Icons.CASINO_OUTLINED)]),
    ], spacing=10))

    if s == "dh":
        hp = dh.hit_points(u["gen_attrs"])
        summary = f"Životy {hp} · hranice smrti {dh.death_threshold(u['gen_attrs'])} · peníze 1k10+30 zl"
    else:
        hp = drd.hit_points(u["gen_cls"], u["gen_attrs"])
        summary = f"Životy na 1. úrovni {hp} (základ {drd.HP_TABLE[u['gen_cls']][0]} + oprava ODL)"

    can_create = not (s == "dh" and manual and left != 0)

    def create(e):
        c = model.create_character(s, u.get("gen_name", ""), u["gen_race"], u["gen_cls"], u["gen_attrs"])
        app.add_character(c)
        app.open_character(c["id"])

    controls = [
        k.muted("PRAVIDLA", size=12, weight=ft.FontWeight.BOLD),
        k.pills([dh.NAME, drd.NAME], r.NAME, set_sys, equal=True),
        name,
        k.muted("RASA", size=12, weight=ft.FontWeight.BOLD),
        k.pills(races, u["gen_race"], set_race),
        k.muted("POVOLÁNÍ", size=12, weight=ft.FontWeight.BOLD),
        k.pills(classes, u["gen_cls"], set_cls),
        attrs_card,
        k.muted(summary),
        k.button("Vytvořit postavu" if can_create else f"Rozděl ještě {left} bodů", create, disabled=not can_create),
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
