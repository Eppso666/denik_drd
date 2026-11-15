"""Pomocníci postavy DrD: přátelé kouzelníka (kočka, havran, ďáblík) a psi hraničáře."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules import drd_obory
from ..rules.common import d

# které vlastnosti pomocníka ukázat v okénkách (zbytek v řádku pod nimi)
TILE_KEYS = [("Životy", "ŽIVOTY"), ("Životaschopnost", "ŽS"), ("Útočné číslo", "ÚČ"), ("Obranné číslo", "OČ"), ("Odolnost", "ODL"),
             ("Inteligence", "INT"), ("Charisma", "CHA"), ("Magenergie", "MAG"), ("Počet kouzel", "KOUZEL"),
             ("Bojovnost", "BOJ")]


def kind_for(c: dict) -> str | None:
    if c.get("system") != "drd":
        return None
    return {"Kouzelník": "přítel", "Hraničář": "pes"}.get(c.get("cls"))


def add_button(app, c: dict) -> ft.Control | None:
    """Malé tlačítko + vedle nadpisu Vlastnosti (jen kouzelník a hraničář)."""
    kind = kind_for(c)
    if not kind:
        return None
    l = app.look
    return ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_color=l.accent, icon_size=22,
                         tooltip="Přidat přítele" if kind == "přítel" else "Přidat psa",
                         on_click=lambda e: open_picker(app, c))


def _numeric(v: str) -> str:
    """Z „(+1 + 2) = 3, drápy“ udělá „3“ pro okénko; jinak vrátí původní text."""
    s = str(v)
    if "=" in s:
        s = s.split("=", 1)[1]
    return s.split(",")[0].strip()


def open_picker(app, c: dict) -> None:
    k = app.kit
    l = app.look
    kind = kind_for(c)
    owned = {x["name"] for x in c.get("companions", [])}
    rows: list[ft.Control] = []
    if kind == "přítel":
        intro = drd_obory.FAMILIAR_NOTE
        if c["level"] < drd_obory.FAMILIAR_LEVEL:
            intro += f" Tvůj kouzelník je na {c['level']}. úrovni – přítele si podle pravidel povolá až od 3. úrovně."
        pool = drd_obory.FAMILIARS
    else:
        intro = drd_obory.DOG_NOTE
        pool = drd_obory.DOGS

    def pick(name):
        def h(e):
            app.close_dialog()
            add_companion(app, c, kind, name)
        return h

    for x in pool:
        sub = x["special"]
        if kind == "pes":
            sub = f"k% {x['roll'][0]}–{x['roll'][1]} · " + sub
        disabled = kind == "přítel" and x["name"] in owned
        rows.append(k.row_item(x["name"], "už má" if disabled else "", sub=sub,
                               on_click=None if disabled else pick(x["name"])))

    def roll_dog(e):
        r = d(100)
        dog = drd_obory.dog_for_roll(r)
        app.close_dialog()
        model.add_history(c, "Hod na psa", f"k% = {r}")
        if dog:
            add_companion(app, c, "pes", dog["name"])
            app.toast(f"Padlo {r}: {dog['name']}.")
        else:
            app.save(c)
            app.toast(f"Padlo {r} – tentokrát pes není (šance {drd_obory.DOG_CHANCE} %). Zkus to při dalším postupu.")

    content: list[ft.Control] = [k.muted(intro, size=13), k.list_card(rows)]
    actions: list[ft.Control] = [ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]
    if kind == "pes":
        actions.insert(0, ft.TextButton("Hodit k% na psa", on_click=roll_dog))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Přítel kouzelníka" if kind == "přítel" else "Pes hraničáře", size=19,
                     weight=ft.FontWeight.BOLD, head=True),
        bgcolor=l.card, content=ft.Container(ft.Column(content, spacing=10, tight=True, scroll=ft.ScrollMode.AUTO),
                                             width=380),
        actions=actions, scrollable=True,
    ))


def add_companion(app, c: dict, kind: str, name: str) -> None:
    comp = {"id": model.new_id(), "kind": kind, "name": name, "nick": "", "since": c["level"], "overrides": {},
            "note": ""}
    c.setdefault("companions", []).append(comp)
    model.add_history(c, "Pomocník", name)
    app.save(c)
    app.refresh()


def companion_cards(app, c: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    out: list[ft.Control] = []
    for comp in c.get("companions", []):
        stats = drd_obory.companion_stats(comp, c["cls"], c["level"], c.get("branch"))
        dfn = drd_obory.companion_def(comp["kind"], comp["name"])
        tiles = []
        for key, short in TILE_KEYS:
            if key in stats:
                tiles.append(ft.Container(k.stat(short, _numeric(stats[key])), width=64))
        extra = [f"{key}: {stats[key]}" for key in ("Velikost", "Pohyblivost", "Vytrvalost", "Zranitelnost", "Váha",
                                                     "Zkušenost") if key in stats]
        title = comp["name"] + (f" „{comp['nick']}“" if comp.get("nick") else "")
        badge = None
        if comp["kind"] == "pes" and c["level"] - int(comp.get("since", c["level"])) >= 5:
            badge = "ZESÍLIL"
        elif comp["kind"] == "přítel" and c.get("branch") == "Čaroděj" and c["level"] >= 6:
            badge = "ČARODĚJ"
        head = ft.Row([
            ft.Column([k.text(title, size=16, weight=ft.FontWeight.BOLD, head=True),
                       k.muted(dfn["special"] if dfn else "", size=12)], spacing=2, expand=True),
            *([k.badge(badge)] if badge else []),
            ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=l.muted, tooltip="Upravit",
                          on_click=lambda e, comp=comp: edit_companion(app, c, comp)),
        ], vertical_alignment=ft.CrossAxisAlignment.START)
        body = [head, ft.Row(tiles, spacing=6, wrap=True, run_spacing=6), k.muted(" · ".join(extra), size=12)]
        if comp.get("note"):
            body.append(k.muted(comp["note"], size=12, italic=True))
        out.append(k.card(ft.Column(body, spacing=8)))
    return out


def edit_companion(app, c: dict, comp: dict) -> None:
    stats = drd_obory.companion_stats(comp, c["cls"], c["level"], c.get("branch"))
    fields = [("nick", "Jméno (volitelné)", comp.get("nick", ""), "text"),
              ("since", "U pána od úrovně", comp.get("since", c["level"]), "int"),
              ("hp", "Životy (poznámka)", comp.get("overrides", {}).get("Životy", ""), "text"),
              ("note", "Poznámka", comp.get("note", ""), "long")]

    def save(v):
        comp["nick"] = v["nick"].strip()
        comp["since"] = max(1, int(v["since"]))
        comp["note"] = v["note"].strip()
        if v["hp"].strip():
            comp.setdefault("overrides", {})["Životy"] = v["hp"].strip()
        else:
            comp.get("overrides", {}).pop("Životy", None)
        app.save(c)
        app.refresh()

    def delete():
        c["companions"].remove(comp)
        app.save(c)
        app.refresh()

    app.form(comp["name"], fields, save, on_delete=delete)

