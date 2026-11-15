"""Řízení aplikace: stav, ukládání, navigace mezi obrazovkami a dialogy."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

import flet as ft

from . import model, theme
from .storage import Storage
from .ui.kit import Kit


@dataclass
class Screen:
    title: str
    controls: list[ft.Control]
    fab: ft.Control | None = None
    actions: list[ft.Control] | None = None


# obrazovka -> rodič (None = kořen se spodní navigací)
MAX_WIDTH = 640  # maximální šířka obsahu v px (vzhled jako na telefonu i na PC)

PARENTS: dict[str, str | None] = {
    "start": None,
    "generator": "start",
    "postava": None,
    "batoh": None,
    "kostky": None,
    "bestiar": None,
    "denik": None,
    "souboj": "kostky",
    "postup": "postava",
    "dovednosti": "postava",
}
NAV = [("postava", "Postava", ft.Icons.PERSON_OUTLINE), ("batoh", "Batoh", ft.Icons.BACKPACK_OUTLINED),
       ("kostky", "Kostky", ft.Icons.CASINO_OUTLINED), ("bestiar", "Bestiář", ft.Icons.PETS_OUTLINED),
       ("denik", "Deník", ft.Icons.MENU_BOOK_OUTLINED)]


class App:
    def __init__(self, page: ft.Page, fonts: set[str]):
        self.page = page
        self.fonts = fonts
        self.store = Storage(page)
        self.picker = ft.FilePicker()
        self.chars: dict[str, dict] = {}
        self.order: list[str] = []
        self.bestiary: dict[str, list[dict]] = {"dh": [], "drd": []}
        self.settings: dict[str, Any] = {"dh_exploding": True}
        self.active: str | None = None
        self.screen = "start"
        self.ui: dict[str, Any] = {}
        self.images: dict[str, bytes] = {}
        self._loading_images: set[str] = set()

    # --- stav ----------------------------------------------------------------
    @property
    def char(self) -> dict | None:
        return self.chars.get(self.active) if self.active else None

    @property
    def system(self) -> str | None:
        c = self.char
        return c["system"] if c and self.screen not in ("start", "generator") else None

    @property
    def look(self) -> theme.Look:
        if self.screen == "generator":
            return theme.for_system(self.ui.get("gen_sys", "dh"))
        return theme.for_system(self.system)

    @property
    def kit(self) -> Kit:
        look = self.look
        return Kit(look, theme.head(look, self.fonts))

    async def load(self) -> None:
        self.order = await self.store.get_json("order", [])
        for cid in list(self.order):
            c = await self.store.get_json("char." + cid, None)
            if c:
                self.chars[cid] = c
            else:
                self.order.remove(cid)
        self.bestiary["dh"] = await self.store.get_json("bestiary.dh", [])
        self.bestiary["drd"] = await self.store.get_json("bestiary.drd", [])
        self.settings.update(await self.store.get_json("settings", {}))

    def save(self, c: dict | None = None, bestiary: str | None = None, settings: bool = False) -> None:
        async def _save():
            try:
                if c is not None:
                    await self.store.set_json("char." + c["id"], c)
                    await self.store.set_json("order", self.order)
                if bestiary:
                    await self.store.set_json("bestiary." + bestiary, self.bestiary[bestiary])
                if settings:
                    await self.store.set_json("settings", self.settings)
            except Exception as ex:  # pragma: no cover - zobrazí se uživateli
                self.toast(f"Uložení se nepovedlo: {ex}")
        self.page.run_task(_save)

    def add_character(self, c: dict) -> None:
        self.chars[c["id"]] = c
        self.order.insert(0, c["id"])
        self.save(c)

    async def delete_character(self, cid: str) -> None:
        c = self.chars.pop(cid, None)
        if cid in self.order:
            self.order.remove(cid)
        if c:
            for img in c.get("images", []):
                await self.store.delete_image(img["ref"])
        await self.store.remove("char." + cid)
        await self.store.set_json("order", self.order)

    # --- navigace ------------------------------------------------------------
    def open_character(self, cid: str) -> None:
        self.active = cid
        self.go("postava")

    def go(self, screen: str, **ui: Any) -> None:
        self.screen = screen
        self.ui.update(ui)
        self.render()

    def back(self) -> None:
        parent = PARENTS.get(self.screen)
        if parent:
            self.go(parent)
        elif self.screen != "start":
            self.active = None
            self.go("start")

    def refresh(self) -> None:
        self.render()

    def render(self) -> None:
        from .ui import screens

        look = self.look
        theme.apply(self.page, look, self.fonts)
        k = self.kit
        sc: Screen = screens.build(self)
        parent = PARENTS.get(self.screen)
        is_char_root = self.system is not None and parent is None
        leading = None
        if parent or self.screen not in ("start", "postava", "batoh", "kostky", "bestiar", "denik"):
            leading = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=look.ink, on_click=lambda e: self.back(),
                                    tooltip="Zpět")
        elif is_char_root:
            leading = ft.IconButton(icon=ft.Icons.PEOPLE_OUTLINE, icon_color=look.ink, tooltip="Výběr postavy",
                                    on_click=lambda e: self.back())
        appbar = ft.AppBar(
            leading=leading, title=k.title(sc.title, size=21), bgcolor=look.bg, color=look.ink,
            actions=sc.actions or [], center_title=False,
        )
        nav = None
        if is_char_root:
            idx = [n[0] for n in NAV].index(self.screen) if self.screen in [n[0] for n in NAV] else 0
            nav = ft.NavigationBar(
                destinations=[ft.NavigationBarDestination(icon=ic, label=lbl) for _, lbl, ic in NAV],
                selected_index=idx, bgcolor=look.nav_bg,
                indicator_color=look.accent if look.dark else look.card,
                on_change=lambda e: self.go(NAV[e.control.selected_index][0]),
            )
        # Na širokém displeji (PC) drží aplikace šířku telefonu/tabletu a je vycentrovaná;
        # na telefonu je MAX_WIDTH větší než displej, takže se nic nemění.
        frame = ft.Pagelet(
            content=ft.Column(sc.controls, spacing=0, expand=True),
            appbar=appbar, navigation_bar=nav, floating_action_button=sc.fab,
            bgcolor=look.bg, expand=True, max_width=MAX_WIDTH,
        )
        view = ft.View(
            route="/" + self.screen, controls=[frame], bgcolor=look.border if not look.dark else "#0b0a0d",
            padding=0, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        views: list[ft.View] = []
        if leading is not None and parent:
            views.append(ft.View(route="/", controls=[], bgcolor=look.bg))
        views.append(view)
        self.page.views.clear()
        self.page.views.extend(views)
        self.page.update()

    async def on_view_pop(self, e) -> None:
        self.back()

    # --- dialogy -------------------------------------------------------------
    def run(self, res: Any) -> None:
        """Spustí výsledek obsluhy, pokud je to korutina."""
        if asyncio.iscoroutine(res):
            async def runner():
                await res
            self.page.run_task(runner)

    def toast(self, message: str) -> None:
        self.page.show_dialog(ft.SnackBar(ft.Text(message)))

    def close_dialog(self) -> None:
        try:
            self.page.pop_dialog()
        except Exception:
            pass

    def confirm(self, title: str, text: str, on_yes: Callable[[], Any], yes_label: str = "Smazat") -> None:
        k = self.kit

        def yes(e):
            self.close_dialog()
            self.run(on_yes())

        self.page.show_dialog(ft.AlertDialog(
            title=k.text(title, size=19, weight=ft.FontWeight.BOLD), content=k.text(text),
            bgcolor=self.look.card,
            actions=[ft.TextButton("Zrušit", on_click=lambda e: self.close_dialog()),
                     ft.TextButton(yes_label, on_click=yes)],
        ))

    def form(self, title: str, fields: list[tuple], on_save: Callable[[dict], Any], save_label: str = "Uložit",
             on_delete: Callable[[], Any] | None = None) -> None:
        """Obecný formulář. Pole: (klíč, popisek, hodnota, druh[, volby]). Druhy: text, long, int, float, bool, choice."""
        look = self.look
        k = self.kit
        controls: dict[str, ft.Control] = {}
        body: list[ft.Control] = []
        for f in fields:
            key, label, value, kind = f[0], f[1], f[2], f[3]
            if kind == "bool":
                ctrl = ft.Switch(label=label, value=bool(value), active_color=look.accent)
            elif kind == "choice":
                opts = f[4]
                ctrl = ft.Dropdown(label=label, value=str(value) if value is not None else None,
                                   options=[ft.DropdownOption(key=o, text=o) for o in opts], expand=True,
                                   border_color=look.border, focused_border_color=look.accent, color=look.ink)
            else:
                ctrl = ft.TextField(
                    label=label, value="" if value is None else str(value),
                    multiline=kind == "long", min_lines=3 if kind == "long" else None,
                    max_lines=8 if kind == "long" else 1,
                    keyboard_type=ft.KeyboardType.NUMBER if kind in ("int", "float") else ft.KeyboardType.TEXT,
                    border_color=look.border, focused_border_color=look.accent, color=look.ink,
                    cursor_color=look.accent,
                )
            controls[key] = ctrl
            body.append(ctrl)

        def collect() -> dict:
            out: dict = {}
            for f in fields:
                key, kind = f[0], f[3]
                c = controls[key]
                v = c.value
                if kind == "int":
                    try:
                        v = int(str(v).replace(",", ".").split(".")[0] or 0)
                    except ValueError:
                        v = 0
                elif kind == "float":
                    try:
                        v = float(str(v).replace(",", ".") or 0)
                    except ValueError:
                        v = 0.0
                elif kind == "bool":
                    v = bool(v)
                out[key] = v
            return out

        def save(e):
            data = collect()
            self.close_dialog()
            self.run(on_save(data))

        actions: list[ft.Control] = []
        if on_delete:
            def delete(e):
                self.close_dialog()
                self.confirm("Opravdu smazat?", "Tuto akci nejde vrátit.", on_delete)
            actions.append(ft.TextButton("Smazat", on_click=delete, style=ft.ButtonStyle(color=look.bad)))
        actions += [ft.TextButton("Zrušit", on_click=lambda e: self.close_dialog()),
                    ft.FilledButton(content=ft.Text(save_label), on_click=save,
                                    style=ft.ButtonStyle(bgcolor=look.accent, color=look.on_accent))]
        self.page.show_dialog(ft.AlertDialog(
            title=k.text(title, size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=look.card,
            content=ft.Container(ft.Column(body, spacing=10, tight=True, scroll=ft.ScrollMode.AUTO), width=360),
            actions=actions, scrollable=True,
        ))

    # --- obrázky -------------------------------------------------------------
    def image_bytes(self, ref: str) -> bytes | None:
        if ref in self.images:
            return self.images[ref]
        if ref not in self._loading_images:
            self._loading_images.add(ref)

            async def load():
                data = await self.store.load_image(ref)
                if data:
                    self.images[ref] = data
                    self.render()
            self.page.run_task(load)
        return None

    async def pick_image(self) -> bytes | None:
        files = await self.picker.pick_files(
            dialog_title="Vyber obrázek", file_type=ft.FilePickerFileType.IMAGE, with_data=True,
            compression_quality=0 if not getattr(self.page, "web", False) else 60,
        )
        if not files:
            return None
        f = files[0]
        data = getattr(f, "bytes", None)
        if not data and getattr(f, "path", None):
            with open(f.path, "rb") as fh:
                data = fh.read()
        return data


def new_char_defaults() -> dict:
    return {"gen_sys": "dh", "gen_mode": "auto", "gen_race": None, "gen_cls": None, "gen_attrs": None,
            "gen_points": None, "gen_name": ""}


__all__ = ["App", "Screen", "model"]
