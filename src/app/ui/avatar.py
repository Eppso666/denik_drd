"""Portrét postavy: obrázek v kroužku, jinak iniciály."""
from __future__ import annotations

import flet as ft

from .. import model


def initials(c: dict) -> str:
    return "".join(p[0] for p in c["name"].split()[:2]).upper() or "?"


def avatar(app, c: dict, size: int, radius: int, accent: str, bg: str, border: int = 2,
           font_family: str | None = None, on_click=None) -> ft.Control:
    """Kroužek s portrétem postavy (nebo iniciálami, dokud obrázek není nahraný)."""
    ref = c.get("avatar")
    data = app.image_bytes(ref) if ref else None
    if data:
        inner = ft.Image(src=data, width=size, height=size, fit=ft.BoxFit.COVER,
                         border_radius=ft.BorderRadius.all(radius))
    else:
        inner = ft.Text(initials(c), size=round(size * 0.35), weight=ft.FontWeight.BOLD, color=accent,
                        font_family=font_family)
    return ft.Container(
        inner, width=size, height=size, alignment=ft.Alignment.CENTER, bgcolor=bg,
        border=ft.Border.all(border, accent), border_radius=ft.BorderRadius.all(radius),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, on_click=on_click,
        tooltip="Změnit portrét" if on_click else None,
    )


async def pick_avatar(app, c: dict) -> None:
    data = await app.pick_image()
    if not data:
        return
    if c.get("avatar"):
        await app.store.delete_image(c["avatar"])
    ref = await app.store.save_image(model.new_id(), data)
    app.images[ref] = data
    c["avatar"] = ref
    app.save(c)
    app.refresh()


async def remove_avatar(app, c: dict) -> None:
    if c.get("avatar"):
        await app.store.delete_image(c["avatar"])
    c["avatar"] = None
    app.save(c)
    app.refresh()


def avatar_menu(app, c: dict) -> None:
    """Dialog: nahrát / změnit / odebrat portrét."""
    k = app.kit
    l = app.look

    def choose(e):
        app.close_dialog()
        app.run(pick_avatar(app, c))

    def remove(e):
        app.close_dialog()
        app.run(remove_avatar(app, c))

    actions: list[ft.Control] = []
    if c.get("avatar"):
        actions.append(ft.TextButton("Odebrat", on_click=remove, style=ft.ButtonStyle(color=l.bad)))
    actions += [ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()),
                ft.FilledButton(content=ft.Text("Vybrat obrázek"), on_click=choose,
                                style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))]
    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Portrét postavy", size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=k.muted("Vyber obrázek z galerie nebo z disku. Zobrazí se v kroužku místo iniciál.", size=14),
        actions=actions,
    ))
