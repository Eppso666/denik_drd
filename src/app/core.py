"""Řízení aplikace: stav, ukládání, navigace mezi obrazovkami a dialogy."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable

import flet as ft

from . import model, stul, sync, theme
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
    "kouzla": "postava",
    "obor": "postava",
    "alchymie": "postava",
    "druzina": "postava",
    "katalog": "batoh",
    # Pán jeskyně (Stůl PJ) – kořeny se spodní navigací PJ
    "pj_kampan": None,
    "pj_souboj": None,
    "pj_bestiar": None,
    "pj_nastroje": None,
    "pj_poznamky": None,
    # propojení a průvodce
    "propojeni": "start",
    "pruvodce": "start",
    "pj_login": "start",
}
PJ_ROOTS = ("pj_kampan", "pj_souboj", "pj_bestiar", "pj_nastroje", "pj_poznamky")
SETUP = ("propojeni", "pruvodce", "pj_login")
NAV = [("postava", "Postava", ft.Icons.PERSON_OUTLINE), ("batoh", "Batoh", ft.Icons.BACKPACK_OUTLINED),
       ("kostky", "Kostky", ft.Icons.CASINO_OUTLINED), ("bestiar", "Bestiář", ft.Icons.PETS_OUTLINED),
       ("denik", "Deník", ft.Icons.MENU_BOOK_OUTLINED)]
PJ_NAV = [("pj_kampan", "Kampaň", ft.Icons.GROUPS_OUTLINED), ("pj_souboj", "Souboj", ft.Icons.SPORTS_MARTIAL_ARTS),
          ("pj_bestiar", "Bestiář", ft.Icons.PETS_OUTLINED), ("pj_nastroje", "Nástroje", ft.Icons.AUTO_FIX_HIGH),
          ("pj_poznamky", "Poznámky", ft.Icons.HISTORY_EDU_OUTLINED)]


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
        # Pozice posuvníku: překreslení téže obrazovky (krokování +/−, výběr karty) nesmí skočit nahoru.
        self._scroll: dict[str, float] = {}
        self._rendered: str | None = None
        self.images: dict[str, bytes] = {}
        self._loading_images: set[str] = set()
        self._sync_loop = False
        # Pán jeskyně: kampaně v tomto zařízení (bez postavy), otevřená kampaň, stoly a spojení
        self.gm: dict[str, dict] = {}
        self.gm_order: list[str] = []
        self.gm_active: str | None = None
        self.hosts: dict[str, stul.Host] = {}
        self._clients: dict[str, Any] = {}
        self.pj_content: dict = {}

    # --- stav ----------------------------------------------------------------
    @property
    def char(self) -> dict | None:
        return self.chars.get(self.active) if self.active else None

    @property
    def camp(self) -> dict | None:
        """Kampaň PJ otevřená na Stole PJ."""
        return self.gm.get(self.gm_active) if self.gm_active else None

    @property
    def system(self) -> str | None:
        if self.screen in PJ_ROOTS:
            camp = self.camp
            return camp["system"] if camp else None
        if self.screen in SETUP:
            return self.ui.get("new_sys") or (self.camp or {}).get("system")
        c = self.char
        return c["system"] if c and self.screen not in ("start", "generator") else None

    @property
    def look(self) -> theme.Look:
        if self.screen == "generator":  # společná obrazovka: neutrální vzhled, hra se vybírá kartami
            return theme.for_system(None)
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
        self.gm_order = await self.store.get_json("gm_order", [])
        for cid in list(self.gm_order):
            camp = await self.store.get_json("gm." + cid, None)
            if camp:
                self.gm[cid] = camp
            else:
                self.gm_order.remove(cid)
        self.pj_content = await self.store.get_json("pj_content", {})
        if any(sync.is_remote(sync.campaign(c)) for c in self.chars.values()) or self.gm:
            self.start_sync_loop()

    def take_invite(self, text: str | None) -> None:
        """Pozvánka z odkazu: předvyplní se v Družině postavy (Zadat ručně)."""
        if text and sync.parse_invite(text):
            self.ui["invite_text"] = text
            self.ui["join_tab"] = "Zadat ručně"

    # --- družina: spojení ----------------------------------------------------
    def client(self, srv: dict | None, camp: dict | None = None) -> "sync.Backend":
        """Spojení pro kampaň: stůl PJ (místně), stůl jiného PJ (Wi-Fi) nebo vlastní server (Supabase)."""
        srv = srv or sync.legacy_server() or {"kind": "own", "url": "", "key": ""}
        if srv.get("kind") == "table":
            if camp is not None and camp.get("role") == "gm":
                return stul.LocalTable(self.table_state(camp))
            key = "table:" + srv.get("host", "")
            if key not in self._clients:
                self._clients[key] = stul.RemoteTable(self.settings, lambda: self.save(settings=True), srv)
            else:
                self._clients[key].server = srv
            return self._clients[key]
        key = sync.server_key(srv)
        if key not in self._clients:
            self._clients[key] = sync.Client(self.settings, lambda: self.save(settings=True), srv)
        return self._clients[key]

    @property
    def sync(self) -> "sync.Backend":
        """Spojení otevřené postavy (zpětná kompatibilita)."""
        c = self.char
        camp = sync.campaign(c) if c else None
        return self.client(sync.server_of(camp), camp)

    def table_state(self, camp: dict) -> "stul.TableState":
        host = self.hosts.get(camp["id"])
        if host is None:
            state = stul.TableState(camp.get("table") or {"id": camp["id"], "name": camp["name"],
                                                         "system": camp["system"], "code": camp.get("code")})

            def changed():
                camp["table"] = state.dump()
                camp["_dirty"] = True
            state.changed = changed
            host = self.hosts[camp["id"]] = stul.Host(state)
        return host.state

    async def open_table(self, camp: dict) -> bool:
        """Otevře stůl PJ v místní síti (server v telefonu) a nechá displej svítit."""
        self.table_state(camp)
        host = self.hosts[camp["id"]]
        for cid, other in list(self.hosts.items()):  # otevřený je vždy jen jeden stůl
            if cid != camp["id"] and other.running:
                await other.stop()
        ok = await host.start()
        if ok:
            try:
                await ft.Wakelock().enable()
            except Exception:  # pragma: no cover - na PC/webu není
                pass
        return ok

    def save_gm(self, camp: dict) -> None:
        async def _save():
            try:
                await self.store.set_json("gm." + camp["id"], camp)
                await self.store.set_json("gm_order", self.gm_order)
            except Exception as ex:  # pragma: no cover
                self.toast(f"Uložení se nepovedlo: {ex}")
        camp.pop("_dirty", None)
        self.page.run_task(_save)

    def add_gm(self, camp: dict) -> None:
        self.gm[camp["id"]] = camp
        if camp["id"] not in self.gm_order:
            self.gm_order.insert(0, camp["id"])
        self.save_gm(camp)
        self.start_sync_loop()

    async def delete_gm(self, cid: str) -> None:
        camp = self.gm.pop(cid, None)
        if cid in self.gm_order:
            self.gm_order.remove(cid)
        host = self.hosts.pop(cid, None)
        if host:
            await host.stop()
        for m in (camp or {}).get("maps", []):
            if m.get("ref"):
                await self.store.delete_image(m["ref"])
        await self.store.remove("gm." + cid)
        await self.store.set_json("gm_order", self.gm_order)
        if self.gm_active == cid:
            self.gm_active = None

    def open_gm(self, cid: str) -> None:
        self.gm_active = cid
        self.active = None
        camp = self.gm[cid]
        if sync.is_table(camp):
            self.run(self.open_table(camp))
        self.go("pj_kampan")
        self.start_sync_loop()

    async def sync_gm_now(self, camp: dict) -> bool:
        changed = await sync.sync_gm(self.client(camp.get("server"), camp), camp)
        if camp.get("gone"):
            await self.delete_gm(camp["id"])
            self.toast("Kampaň na serveru už není.")
            if self.screen in PJ_ROOTS:
                self.go("start")
            return True
        self.save_gm(camp)
        return changed

    def start_sync_loop(self) -> None:
        """Na pozadí každých pár sekund: postava v kampani (hráč) a otevřená kampaň PJ."""
        if self._sync_loop or sync.SYNC_INTERVAL is None:
            return
        self._sync_loop = True

        async def loop():
            while True:
                await asyncio.sleep(sync.SYNC_INTERVAL)
                try:
                    c = self.char
                    if c and sync.is_remote(sync.campaign(c)):
                        pc = sync.campaign(c)
                        res = await sync.sync_player(self.client(sync.server_of(pc)), c)
                        if sync.is_table(pc) and not pc.get("online") and time.time() - pc.get("_found", 0) > 60:
                            pc["_found"] = time.time()  # telefon PJ mohl dostat jinou adresu na Wi-Fi
                            hit = next((t for t in await stul.find_tables()
                                        if t.get("code") == pc["server"].get("code")), None)
                            if hit:
                                pc["server"]["host"] = hit["host"]
                        await self.after_sync(c, res)
                    camp = self.camp
                    if camp and self.screen in PJ_ROOTS:
                        if await self.sync_gm_now(camp):
                            self.refresh()
                    for cid, host in self.hosts.items():  # stav stolu do telefonu PJ
                        g = self.gm.get(cid)
                        if g and g.get("_dirty"):
                            self.save_gm(g)
                except Exception:  # pragma: no cover - síť nesmí shodit aplikaci
                    pass
        self.page.run_task(loop)

    async def after_sync(self, c: dict, res) -> None:
        """Uloží stav, stáhne nové obrázky od PJ do Deníku a překreslí obrazovku Družina."""
        changed = res.get("changed") if isinstance(res, dict) else bool(res)
        notice = res.get("notice") if isinstance(res, dict) else None
        camp = sync.campaign(c)
        if not camp:
            return
        if camp.get("gone"):
            why = camp.get("gone")
            sync.leave(c)
            self.save(c)
            self.toast("PJ tvou žádost nepřijal." if why == "rejected" else
                       "Kampaň byla ukončena nebo tě PJ vyřadil. Postava ti zůstala.")
            if self.screen == "druzina":
                self.refresh()
            return
        if notice:
            self.toast(notice)
        saved = camp.setdefault("saved_images", [])
        for img in camp.get("images") or []:
            if img["path"] in saved:
                continue
            try:
                data = await self.client(sync.server_of(camp)).download_image(img["path"])
            except Exception:
                break
            ref = await self.store.save_image(model.new_id(), data)
            self.images[ref] = data
            c["images"].insert(0, {"id": model.new_id(), "ref": ref, "title": img.get("title") or "Od PJ",
                                   "category": "Mapa", "ts": time.time()})
            saved.append(img["path"])
            changed = True
        self.save(c)
        if changed and self.screen in ("druzina", "postava"):
            self.refresh()

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
            if c.get("avatar"):
                await self.store.delete_image(c["avatar"])
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
        if self.screen == "pruvodce" and self.ui.get("wiz_step", 1) > 1:
            self.ui["wiz_step"] -= 1
            self.render()
        elif parent:
            self.go(parent)
        elif self.screen != "start":
            self.active = None
            self.gm_active = None
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
        pj_root = self.screen in PJ_ROOTS
        is_char_root = self.system is not None and parent is None and not pj_root and self.screen not in SETUP
        leading = None
        if parent or self.screen not in ("start", "postava", "batoh", "kostky", "bestiar", "denik", *PJ_ROOTS):
            leading = ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=look.ink, on_click=lambda e: self.back(),
                                    tooltip="Zpět")
        elif is_char_root or pj_root:
            leading = ft.IconButton(icon=ft.Icons.PEOPLE_OUTLINE, icon_color=look.ink,
                                    tooltip="Postavy a kampaně", on_click=lambda e: self.back())
        header = self._header(look, sc, leading)
        nav = self._nav(look, PJ_NAV if pj_root else NAV) if (is_char_root or pj_root) else None
        # Na širokém displeji (PC) drží aplikace šířku telefonu/tabletu a je vycentrovaná;
        # na telefonu je MAX_WIDTH větší než displej, takže se nic nemění.
        body = [header, ft.Container(ft.Column(sc.controls, spacing=0, expand=True), expand=True)]
        frame = ft.Pagelet(
            content=ft.Container(ft.Column(body, spacing=0, expand=True), expand=True,
                                 gradient=ft.RadialGradient(center=ft.Alignment.TOP_CENTER, radius=1.6,
                                                            colors=[look.bg2, look.bg])),
            bottom_appbar=ft.BottomAppBar(content=nav, padding=ft.Padding.all(0), height=78, bgcolor=look.bg,
                                          elevation=0) if nav is not None else None,
            floating_action_button=sc.fab, bgcolor=look.bg, expand=True, max_width=MAX_WIDTH,
        )
        view = ft.View(
            route="/" + self.screen, controls=[frame], bgcolor="#07060a",
            padding=0, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        views: list[ft.View] = []
        if leading is not None and parent:
            views.append(ft.View(route="/", controls=[], bgcolor=look.bg))
        views.append(view)
        self.page.views.clear()
        self.page.views.extend(views)
        self._keep_scroll(sc)
        self.page.update()
        self._restore_scroll()

    def _header(self, look, sc: "Screen", leading) -> ft.Control:
        """Horní lišta podle návrhu: přechod, kovová linka, nadpis s ornamenty a kosočtverec uprostřed."""
        k = self.kit
        orn = lambda: ft.Container(width=18, height=1, bgcolor=look.frame)  # noqa: E731
        title = ft.Row([orn(), k.text(sc.title, size=20, weight=ft.FontWeight.BOLD, head=True, max_lines=1),
                        orn()], spacing=10, alignment=ft.MainAxisAlignment.CENTER, tight=True)
        actions = list(sc.actions or [])
        left = leading or ft.Container(width=40)
        while len(actions) < 1:
            actions.append(ft.Container(width=40))
        bar = ft.Container(
            content=ft.Row([left, ft.Container(title, expand=True, alignment=ft.Alignment.CENTER), *actions],
                           spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            height=60, padding=ft.Padding.symmetric(horizontal=6),
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                                       colors=[look.bg2, look.bg]),
            border=ft.Border.only(bottom=ft.BorderSide(1, look.frame)),
        )
        gem = ft.Container(width=9, height=9, bgcolor=look.orn, rotate=ft.Rotate(0.785),
                           border=ft.Border.all(1, look.bg))
        return ft.Stack([bar, ft.Row([gem], alignment=ft.MainAxisAlignment.CENTER, left=0, right=0, bottom=-4)],
                        clip_behavior=ft.ClipBehavior.NONE, height=60)

    def _nav(self, look, nav=None) -> ft.Control:
        """Spodní navigace podle návrhu: aktivní položka svítí akcentem (hráč nebo Stůl PJ)."""
        items = []
        for key, label, icon in nav or NAV:
            on = key == self.screen
            fg = look.on_accent if on else look.ink
            items.append(ft.Container(
                content=ft.Column([ft.Icon(icon, size=24, color=look.on_accent if on else look.orn),
                                   ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=fg, no_wrap=True)],
                                  spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                expand=1, padding=ft.Padding.symmetric(vertical=6), border_radius=ft.BorderRadius.all(look.radius),
                gradient=ft.RadialGradient(colors=[look.accent2, look.accent], radius=1.0) if on else None,
                border=ft.Border.all(1, look.orn if on else "#00000000"),
                shadow=[ft.BoxShadow(blur_radius=14, color=look.glow)] if on else None,
                on_click=lambda e, key=key: self.go(key), ink=True, tooltip=label,
                data=key,
            ))
        return ft.Container(
            content=ft.Row(items, spacing=4), padding=ft.Padding.only(left=8, right=8, top=8, bottom=10),
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                                       colors=[look.bg2, look.bg]),
            border=ft.Border.only(top=ft.BorderSide(1, look.frame)),
        )

    def _main_column(self, sc: "Screen") -> ft.Column | None:
        for ctrl in sc.controls:
            col = getattr(ctrl, "content", None) if isinstance(ctrl, ft.Container) else ctrl
            if isinstance(col, ft.Column) and col.scroll:
                return col
        return None

    def _keep_scroll(self, sc: "Screen") -> None:
        same = self._rendered == self.screen
        self._rendered = self.screen
        if not same:
            self._scroll.pop(self.screen, None)
        self._col = self._main_column(sc)
        if self._col is None:
            return
        screen = self.screen

        def remember(e) -> None:
            self._scroll[screen] = float(getattr(e, "pixels", 0) or 0)
        self._col.on_scroll = remember
        self._col.scroll_interval = 50

    def _restore_scroll(self) -> None:
        off = self._scroll.get(self.screen, 0)
        if self._col is not None and off > 0:
            try:
                self.run(self._col.scroll_to(offset=off, duration=0))
            except Exception:  # pragma: no cover - ovládací prvek ještě není na stránce
                pass

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
                ctrl = ft.Switch(label=label, value=bool(value), active_color=look.hi)
            elif kind == "choice":
                opts = f[4]
                ctrl = ft.Dropdown(label=label, value=str(value) if value is not None else None,
                                   options=[ft.DropdownOption(key=o, text=o) for o in opts], expand=True,
                                   border_color=look.frame, focused_border_color=look.hi, color=look.ink)
            else:
                ctrl = ft.TextField(
                    label=label, value="" if value is None else str(value),
                    multiline=kind == "long", min_lines=3 if kind == "long" else None,
                    max_lines=8 if kind == "long" else 1,
                    keyboard_type=ft.KeyboardType.NUMBER if kind in ("int", "float") else ft.KeyboardType.TEXT,
                    border_color=look.frame, focused_border_color=look.hi, color=look.ink,
                    cursor_color=look.hi,
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

    async def pick_image(self, max_side: int = 1024) -> bytes | None:
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
        return shrink_image(data, max_side) if data else data


def shrink_image(data: bytes, max_side: int = 1024, quality: int = 80) -> bytes:
    """Zmenší obrázek na nejvýš max_side px (JPEG). Bez knihovny Pillow vrátí původní data."""
    try:
        import io

        from PIL import Image, ImageOps
    except Exception:  # pragma: no cover - Pillow není k dispozici
        return data
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        if max(im.size) <= max_side and len(data) <= 300_000:
            return data
        im.thumbnail((max_side, max_side))
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        out = io.BytesIO()
        im.save(out, "JPEG", quality=quality, optimize=True)
        return out.getvalue() if out.tell() < len(data) else data
    except Exception:
        return data


def new_char_defaults() -> dict:
    return {"gen_sys": "dh", "gen_mode": "auto", "gen_race": None, "gen_cls": None, "gen_attrs": None,
            "gen_points": None, "gen_name": ""}


__all__ = ["App", "Screen", "model"]
