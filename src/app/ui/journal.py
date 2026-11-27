"""Bestiář (zvlášť pro každou hru) a deník postavy (poznámky a obrázky)."""
from __future__ import annotations

import time

import flet as ft

from .. import model
from .kit import column

NOTE_TAGS = ["Úkol", "Osoba", "Místo", "Ostatní"]  # „Postava“ je teď samostatná záložka Deníku
IMG_CATS = ["Mapa", "Postava", "Předmět", "Bestiář", "Ostatní"]

DH_FIELDS = [("name", "Jméno", "text"), ("kind", "Druh / prostředí", "text"), ("hp", "Životy", "int"),
             ("uc", "Útočné číslo (ÚČ)", "int"), ("oc", "Obranné číslo (OČ)", "int"), ("dmg", "Zranění", "int"),
             ("special", "Zvláštní schopnost", "text"), ("xp", "Zkušenosti", "int"), ("note", "Poznámka", "long")]
DRD_FIELDS = [("name", "Jméno", "text"), ("kind", "Druh / prostředí", "text"),
              ("zvt", "Životaschopnost", "text"), ("hp", "Životy", "int"), ("uc", "Útok – útočné číslo", "int"),
              ("dmg", "Útok – útočnost", "int"), ("oc", "Obrana (OČ)", "int"), ("odl", "Odolnost", "text"),
              ("inte", "Inteligence", "text"), ("size", "Velikost", "text"), ("zran", "Zranitelnost", "text"),
              ("pohyb", "Pohyblivost", "text"), ("presv", "Přesvědčení", "text"), ("xp", "Zkušenost", "int"),
              ("note", "Poznámka", "long")]


def _thumb(app, ref: str | None, size: int) -> ft.Control:
    l = app.look
    data = app.image_bytes(ref) if ref else None
    if data:
        return ft.Image(src=data, width=size, height=size, fit=ft.BoxFit.COVER,
                        border_radius=ft.BorderRadius.all(l.radius))
    return ft.Container(ft.Icon(ft.Icons.IMAGE_OUTLINED, color=l.muted), width=size, height=size,
                        bgcolor=l.card2, border=ft.Border.all(1, l.border),
                        border_radius=ft.BorderRadius.all(l.radius), alignment=ft.Alignment.CENTER)


# --- bestiář -----------------------------------------------------------------------

def edit_beast(app, b: dict | None) -> None:
    sys = app.char["system"]
    fields = DH_FIELDS if sys == "dh" else DRD_FIELDS
    form = [(key, lbl, (b or {}).get(key, 0 if kind == "int" else ""), kind) for key, lbl, kind in fields]

    def save(v):
        if not str(v["name"]).strip():
            app.toast("Vyplň jméno bytosti.")
            return
        if b is None:
            v["id"] = model.new_id()
            app.bestiary[sys].insert(0, v)
            app.ui["beast_open"] = v["id"]
        else:
            b.update(v)
        app.save(bestiary=sys)
        app.refresh()

    async def delete():
        if b.get("image"):
            await app.store.delete_image(b["image"])
        app.bestiary[sys].remove(b)
        app.save(bestiary=sys)
        app.refresh()

    app.form("Nová bytost" if b is None else "Upravit bytost", form, save, on_delete=delete if b else None)


async def beast_image(app, b: dict) -> None:
    data = await app.pick_image()
    if not data:
        return
    if b.get("image"):
        await app.store.delete_image(b["image"])
    ref = await app.store.save_image(model.new_id(), data)
    app.images[ref] = data
    b["image"] = ref
    app.save(bestiary=app.char["system"])
    app.refresh()


# --- deník -------------------------------------------------------------------------

def denik(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    tab = app.ui.get("journal_tab", "Poznámky")
    body: list[ft.Control] = []
    if tab == "Poznámky":
        notes = sorted(c["notes"], key=lambda n: (not n.get("pinned"), -n.get("ts", 0)))
        for n in notes:
            tag_color = {"Úkol": l.hi, "Osoba": l.mana, "Místo": l.ok}.get(n.get("tag"), l.muted)
            body.append(k.card(ft.Column([
                ft.Row([k.badge((n.get("tag") or "Ostatní").upper() + (" · PŘIPNUTO" if n.get("pinned") else ""),
                                color=tag_color, fg=l.on_accent if l.dark else l.card),
                        k.muted(time.strftime("%d. %m. %Y", time.localtime(n.get("ts", 0))), size=12)],
                       alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                k.text(n.get("title") or "Bez názvu", size=17, weight=ft.FontWeight.BOLD, head=True),
                k.muted(n.get("text", ""), size=14),
            ], spacing=6), on_click=lambda e, n=n: edit_note(app, n)))
        if not notes:
            body.append(k.empty("Zatím žádné zápisky. Zapiš si úkoly, jména a místa z dobrodružství."))
        fab_click = lambda e: edit_note(app, None)  # noqa: E731
    elif tab == "Postava":
        body += postava_tab(app, c)
        fab_click = None
    else:
        cat = app.ui.get("img_cat", "Vše")
        imgs = [i for i in c["images"] if cat == "Vše" or i.get("category") == cat]
        body.append(k.pills(["Vše"] + IMG_CATS, cat, lambda v: app.go("denik", img_cat=v)))
        tiles = []
        for i in imgs:
            tiles.append(ft.Container(ft.Column([
                _thumb(app, i["ref"], 104),
                k.muted(i.get("title") or i.get("category", ""), size=12, max_lines=1),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e, i=i: view_image(app, i)))
        if tiles:
            body.append(ft.Row(tiles, wrap=True, spacing=10, run_spacing=10))
        else:
            body.append(k.empty("Žádné obrázky. Přidej mapu, portrét nebo nákres tlačítkem +."))
        if getattr(app.page, "web", False):
            body.append(k.muted("Webová verze ukládá obrázky v prohlížeči, kde je místo omezené (zhruba 5 MB).",
                                size=12))
        fab_click = lambda e: app.run(add_image(app))  # noqa: E731

    controls = [k.pills(["Poznámky", "Obrázky", "Postava"], tab, lambda v: app.go("denik", journal_tab=v), equal=True),
                *body, ft.Container(height=70)]
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=l.accent, foreground_color=l.on_accent,
                                  tooltip="Přidat", on_click=fab_click) if fab_click else None
    return Screen("Deník", [column(controls)], fab=fab)


def postava_tab(app, c: dict) -> list[ft.Control]:
    """Deník → Postava: přesvědčení (DrD) a příběh postavy."""
    from .character import alignment_card

    k = app.kit
    l = app.look
    out: list[ft.Control] = []
    if c["system"] == "drd":
        out += [k.section("Přesvědčení", icon=ft.Icons.BALANCE), alignment_card(app, c)]
    story = (c.get("story") or "").strip()
    out += [
        k.section("Příběh postavy", k.link("Upravit", lambda e: edit_story(app, c)), icon=ft.Icons.HISTORY_EDU),
        k.parch(ft.Column([
            k.text("Příběh postavy", size=16, weight=ft.FontWeight.BOLD, head=True, color=l.ptext),
            k.text(story or "Zatím nenapsáno. Klepni a napiš, odkud postava pochází, co ji formovalo a co hledá.",
                   size=15, color=l.ptext if story else l.pmuted),
        ], spacing=8)),
    ]
    out[-1] = ft.Container(out[-1], on_click=lambda e: edit_story(app, c), ink=True, data="story")
    return out


def edit_story(app, c: dict) -> None:
    def save(v):
        c["story"] = (v.get("story") or "").strip()
        app.save(c)
        app.refresh()
    app.form("Příběh postavy", [("story", "Příběh postavy", c.get("story", ""), "long")], save)


def edit_note(app, n: dict | None) -> None:
    c = app.char
    g = (lambda key, default: n.get(key, default) if n else default)
    fields = [("title", "Nadpis", g("title", ""), "text"), ("text", "Text", g("text", ""), "long"),
              ("tag", "Štítek", g("tag", "Ostatní"), "choice", NOTE_TAGS), ("pinned", "Připnout nahoru", g("pinned", False), "bool")]

    def save(v):
        if not (v["title"].strip() or v["text"].strip()):
            return
        if n is None:
            v["id"] = model.new_id()
            v["ts"] = time.time()
            c["notes"].append(v)
        else:
            n.update(v)
        app.save(c)
        app.refresh()

    def delete():
        c["notes"].remove(n)
        app.save(c)
        app.refresh()

    app.form("Nový zápis" if n is None else "Upravit zápis", fields, save, on_delete=delete if n else None)


async def add_image(app) -> None:
    c = app.char
    data = await app.pick_image()
    if not data:
        return
    ref = await app.store.save_image(model.new_id(), data)
    app.images[ref] = data
    entry = {"id": model.new_id(), "ref": ref, "title": "", "category": "Mapa", "ts": time.time()}
    c["images"].insert(0, entry)
    app.save(c)

    def save(v):
        entry.update(v)
        app.save(c)
        app.refresh()
    app.refresh()
    app.form("Popis obrázku", [("title", "Název", "", "text"), ("category", "Kategorie", "Mapa", "choice", IMG_CATS)],
             save)


def view_image(app, i: dict) -> None:
    c = app.char
    k = app.kit
    l = app.look
    data = app.image_bytes(i["ref"])

    async def delete():
        await app.store.delete_image(i["ref"])
        c["images"].remove(i)
        app.save(c)
        app.refresh()

    def ask_delete(e):
        app.close_dialog()
        app.confirm("Smazat obrázek?", "Obrázek bude z deníku odstraněn.", delete)

    content = (ft.InteractiveViewer(ft.Image(src=data, fit=ft.BoxFit.CONTAIN), min_scale=1, max_scale=5)
               if data and hasattr(ft, "InteractiveViewer") else
               (ft.Image(src=data, fit=ft.BoxFit.CONTAIN) if data else k.muted("Načítám…")))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(i.get("title") or i.get("category", "Obrázek"), size=18, weight=ft.FontWeight.BOLD),
        content=ft.Container(content, width=360, height=420), bgcolor=l.card,
        actions=[ft.TextButton("Smazat", on_click=ask_delete, style=ft.ButtonStyle(color=l.bad)),
                 ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())],
    ))
