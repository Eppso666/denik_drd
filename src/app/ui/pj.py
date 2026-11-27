"""Stůl PJ – oddělené prostředí Pána jeskyně podle grafického návrhu:
Kampaň (kód pro hráče, hráči se životy a zkušenostmi, úprava hráče), Souboj (jedna iniciativa pro hráče
i nestvůry), Bestiář PJ, Nástroje (zkušenosti za boj) a Poznámky (tajné poznámky, připravené mapy, tajná zpráva).

Kampaň chrání heslo (Doupě pána jeskyně). Kampaň se zakládá na serveru družiny (Supabase); hráči se k ní
připojí kódem v Družině své postavy, bez zámku a bez schvalování. PJ vidí hráče, jejich deníky a hody a sdílí
mapy. Úpravy životů a zkušeností hráčům zatím server neumí – čekají ve frontě kampaně.

Hráč nic z toho nevidí. Obsah příruček PJ je jen v telefonu PJ (nahraný balíček) – ne v aplikaci hráče
ani v repozitáři.
"""
from __future__ import annotations

import json
import random
import time

import flet as ft

from .. import model, sync
from ..rules import dh, drd
from ..rules.common import fmt
from .journal import DH_FIELDS, DRD_FIELDS
from .kit import column

SYS_NAME = {"dh": dh.NAME, "drd": drd.NAME}
PHASES = {"Čas a směny": 8, "Počasí a cesta": 6, "Pasti": 8, "Poklady": 8, "Panství a armády": 9}


# --- místní pomocníci (propojení s hráči je zatím odložené) -------------------------------------------

def players(camp: dict) -> list[dict]:
    """Hráči kampaně (připojení kódem v Družině), PJ mezi nimi není."""
    return [m for m in camp.get("members") or [] if m.get("role", "player") == "player"
            and m.get("status", "approved") == "approved"]


def gm_view_hp(camp: dict, m: dict) -> tuple[int | None, int | None]:
    sh = (camp.get("sheets") or {}).get(m.get("user_id")) or {}
    s = m.get("snapshot") or {}
    hp = sh.get("hp", s.get("hp"))
    hpm = sh.get("hp_max", s.get("hp_max"))
    return (int(hp) if hp is not None else None), (int(hpm) if hpm else None)


def is_online(m: dict) -> bool:
    return bool(m.get("online")) or sync.is_online(m)


def initials(name: str | None) -> str:
    parts = [p for p in (name or "?").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def member_sub(s: dict, lvl: str = "úroveň") -> str:
    bits = [s.get("race"), s.get("cls")]
    if s.get("level"):
        bits.append(f"{s['level']}. {lvl}")
    return " · ".join(str(b) for b in bits if b)


def ago(ts) -> str:
    t = sync._parse_ts(ts) if isinstance(ts, str) else ts
    try:
        sec = max(0, time.time() - float(t))
    except (TypeError, ValueError):
        return ""
    if sec < 90:
        return "právě teď"
    if sec < 3600:
        return f"před {int(sec // 60)} min"
    if sec < 86400:
        return f"před {int(sec // 3600)} h"
    return f"před {int(sec // 86400)} dny"


def info(app, title: str, text: str) -> None:
    k = app.kit
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(title, size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
        content=ft.Container(k.text(text, size=14), width=340),
        actions=[ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]))


def _actions(app, camp) -> list[ft.Control]:
    l = app.look
    return [ft.IconButton(ft.Icons.NOTIFICATIONS_OUTLINED, icon_color=l.ink, tooltip="Oznámení",
                          on_click=lambda e: _notifications(app, camp)),
            ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=l.ink, tooltip="Upravit kampaň",
                          on_click=lambda e: _edit_campaign(app, camp))]


# =============================================================================================== Kampaň

def pj_kampan(app):
    from ..core import Screen

    camp = app.camp
    k = app.kit
    controls: list[ft.Control] = [_head(app, camp)]
    pl = players(camp)
    controls.append(k.section(f"Hráči {len(pl)}", icon=ft.Icons.GROUPS_OUTLINED,
                              trailing=k.link("Rozdělit zkušenosti", lambda e: app.go("pj_nastroje"))))
    if pl:
        controls.append(k.framed(ft.Column([_player_row(app, camp, m, i == len(pl) - 1) for i, m in enumerate(pl)],
                                           spacing=0), padding=ft.Padding.symmetric(horizontal=14)))
    else:
        controls.append(k.empty("Zatím tu nikdo není. Hráči zadají kód kampaně u své postavy v Družině → "
                                "Připojit se." if camp.get("sid") else "Nejdřív získej kód pro hráče."))
    controls.append(k.section("Poslední hody", icon=ft.Icons.CASINO_OUTLINED,
                              trailing=k.link("Vše", lambda e: _all_rolls(app, camp))))
    controls.append(_rolls(app, camp, 5))
    return Screen("Stůl PJ", [column(controls)], actions=_actions(app, camp))


def _head(app, camp) -> ft.Control:
    k = app.kit
    return k.framed(ft.Column([
        ft.Row([ft.Column([k.text(camp["name"], size=21, weight=ft.FontWeight.BOLD, head=True, max_lines=2),
                           k.muted(f"{SYS_NAME[camp['system']]} · sezení {camp['session']}", size=14)],
                          spacing=2, expand=True), k.pj_badge()],
               vertical_alignment=ft.CrossAxisAlignment.START),
        k.divider(),
        (ft.Row([ft.Column([k.muted("Kód pro hráče", size=12),
                            k.text(camp.get("code", "–"), size=26, weight=ft.FontWeight.BOLD, head=True,
                                   color=app.look.hi)], spacing=0, expand=True),
                 k.button("Sdílet", lambda e: share_code(app, camp), primary=False,
                          icon=ft.Icons.SEND_OUTLINED, height=42)], vertical_alignment=ft.CrossAxisAlignment.CENTER)
         if camp.get("sid") else
         ft.Column([k.muted("Kampaň zatím není na serveru družiny – hráči se k ní nemohou připojit.", size=13),
                    k.button("Získat kód pro hráče", lambda e: publish(app, camp), icon=ft.Icons.CLOUD_UPLOAD_OUTLINED,
                             height=44)], spacing=8)),
        *([k.muted(f"Server: {camp['error']}", size=12, color=app.look.bad)] if camp.get("error") else []),
    ], spacing=10), glow=True)


def publish(app, camp, then=None) -> None:
    """Založí kampaň na serveru družiny (dostane kód, který hráči zadají v Družině své postavy)."""
    k = app.kit
    if not sync.configured():
        info(app, "Server není nastavený", "Aplikace nemá nastavený server družiny, hráči se zatím připojit nedají.")
        return

    async def run():
        busy = ft.AlertDialog(modal=True, content=ft.Row([ft.ProgressRing(width=22, height=22, color=app.look.hi),
                                                          k.text("Zakládám kampaň na serveru…", size=15)],
                                                         spacing=14, tight=True))
        app.page.show_dialog(busy)
        try:
            await app.sync.gm_create(camp)
            await app.sync.gm_pull(camp)
            err = None
        except sync.SyncError as ex:
            err = str(ex)
        except OSError:
            err = "Server družiny není dostupný. Zkontroluj internet a zkus to znovu."
        app.close_dialog(busy)
        app.save_gm(camp)
        app.refresh()
        if err:
            info(app, "Kód se nepodařilo získat", err + " Kampaň je uložená, na Stole PJ zkus „Získat kód pro hráče“.")
        else:
            app.toast(f"Kód pro hráče: {camp['code']}")
            app.start_sync_loop()
        if then:
            then()
    app.run(run())


def share_code(app, camp) -> None:
    text = (f"Kód kampaně „{camp['name']}“ ({SYS_NAME[camp['system']]}): {camp.get('code')}. "
            "V Deníku dobrodruha otevři svou postavu → Družina → Připojit se.")

    async def run():
        try:
            await ft.Clipboard().set(text)
        except Exception:  # pragma: no cover - schránka nemusí být dostupná
            pass
        try:
            await ft.Share().share_text(text)
        except Exception:  # pragma: no cover - sdílení není všude
            pass
    app.run(run())
    app.toast(f"Kód {camp.get('code')} zkopírován – pošli ho hráčům.")


def _player_row(app, camp, m, last) -> ft.Control:
    k = app.kit
    l = app.look
    s = m.get("snapshot") or {}
    sh = (camp.get("sheets") or {}).get(m.get("user_id")) or {}
    hp, hpm = gm_view_hp(camp, m)
    online = is_online(m)
    xp = sh.get("xp", s.get("xp"))
    col: list[ft.Control] = [
        ft.Row([k.avatar(initials(s.get("name")), 40),
                ft.Column([ft.Row([ft.Container(width=9, height=9, border_radius=ft.BorderRadius.all(5),
                                                bgcolor=l.ok if online else l.muted),
                                   k.text(s.get("name", "?"), size=16, weight=ft.FontWeight.BOLD, max_lines=1,
                                          expand=True)], spacing=6),
                           k.muted(member_sub(sh or s, "úr."), size=13)], spacing=1, expand=True),
                k.button("Upravit", lambda e: edit_player(app, camp, m), primary=False, icon=ft.Icons.EDIT_OUTLINED,
                         height=40)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ]
    if hp is not None and hpm:
        col.append(ft.Row([ft.Icon(ft.Icons.FAVORITE, size=16, color=l.hp),
                           ft.Container(k.bar(hp, hpm, l.hp, l.hp_dark, height=12), expand=True),
                           ft.Container(k.text(f"{hp}/{hpm}", size=14, weight=ft.FontWeight.BOLD, head=True,
                                               align=ft.TextAlign.RIGHT), width=56)],
                          spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    col.append(ft.Row([
        ft.Row([ft.Icon(ft.Icons.STAR_OUTLINE, size=14, color=l.orn),
                k.muted(f"{fmt_n(xp)} zk." if xp is not None else "zk. –", size=13)], spacing=4, tight=True),
        k.muted("online" if online else "offline · dorovná se", size=13),
        ft.Container(expand=True),
        ft.Container(k.text("Deník ›", size=13, weight=ft.FontWeight.BOLD, color=l.orn),
                     on_click=lambda e: show_sheet(app, camp, m), ink=True,
                     padding=ft.Padding.symmetric(vertical=6, horizontal=4)),
    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return ft.Container(ft.Column(col, spacing=6), padding=ft.Padding.symmetric(vertical=12),
                        border=None if last else ft.Border.only(bottom=ft.BorderSide(1, l.border)))


def fmt_n(n) -> str:
    try:
        return f"{int(n):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(n)


def _rolls(app, camp, n: int) -> ft.Control:
    k = app.kit
    feed = (camp.get("feed") or [])[:n]
    if not feed:
        return k.empty("Zatím žádné hody.")
    return k.list_card([k.row_item(f"{r['who']} · {r['label']}", r["result"],
                                   sub=("vidíš jen ty" if r.get("hidden") else ago(r.get("created_at"))),
                                   badge="SKRYTÝ" if r.get("hidden") else None) for r in feed])


def _all_rolls(app, camp) -> None:
    k = app.kit
    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Hody družiny", size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
        content=ft.Container(ft.Column([_rolls(app, camp, 25)], tight=True, scroll=ft.ScrollMode.AUTO), width=360),
        actions=[ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]))


def _notifications(app, camp) -> None:
    lines = [f"• {r['who']}: {r['label']} = {r['result']}" for r in (camp.get("feed") or [])[:5]]
    if camp.get("outbox"):
        lines.append(f"• {len(camp['outbox'])} úprav pro hráče čeká na propojení")
    info(app, "Oznámení", "\n".join(lines) or "Nic nového.")


def _edit_campaign(app, camp) -> None:
    from .start import check_password, hash_password

    def save(v):
        camp["name"] = (v.get("name") or camp["name"]).strip()[:80]
        camp["session"] = max(1, int(v.get("session") or 1))
        new = v.get("pw_new") or ""
        if new:
            if not check_password(camp, v.get("pw_old") or ""):
                app.toast("Staré heslo nesouhlasí – heslo zůstalo beze změny.")
            elif len(new) < 4:
                app.toast("Nové heslo musí mít aspoň 4 znaky.")
            else:
                camp["pw"] = hash_password(new)
                app.toast("Heslo kampaně změněno.")
        app.save_gm(camp)
        app.refresh()
        if camp.get("sid"):
            async def up():
                try:
                    await app.sync.gm_update(camp)
                except Exception:  # pragma: no cover - síť
                    pass
            app.run(up())

    async def delete():
        if camp.get("sid"):
            try:
                await app.sync.gm_delete(camp)
            except (sync.SyncError, OSError):
                app.toast("Na serveru se kampaň smazat nepodařilo, smazána jen v tomto zařízení.")
        await app.delete_gm(camp["id"])
        app.go("doupe")
        app.toast("Kampaň smazána. Hráčům postavy zůstaly.")
    app.form("Upravit kampaň", [("name", "Název kampaně", camp["name"], "text"),
                                ("session", "Sezení", camp["session"], "int"),
                                ("pw_old", "Staré heslo (jen při změně hesla)", "", "password"),
                                ("pw_new", "Nové heslo", "", "password")],
             save, on_delete=delete)


# --- pohled do deníku hráče ---------------------------------------------------------------------------

def show_sheet(app, camp, m) -> None:
    k = app.kit
    l = app.look

    async def run():
        sh = (camp.get("sheets") or {}).get(m["user_id"])
        if not sh:
            info(app, "Deník", "Hráč zatím deník neposlal.")
            return
        r = drd if camp["system"] == "drd" else dh
        body: list[ft.Control] = [
            k.muted(" · ".join(str(x) for x in (sh.get("race"), sh.get("cls"), sh.get("branch"),
                                                f"{sh.get('level')}. úroveň") if x), size=14),
            k.text(f"Životy {sh.get('hp')}/{sh.get('hp_max')}" + (f" · {sh.get('mana_name') or 'Mana'} "
                                                                    f"{sh.get('mana')}/{sh.get('mana_max')}"
                                                                    if sh.get("mana_max") else ""), size=15,
                   weight=ft.FontWeight.BOLD),
            k.muted(f"Zkušenosti {fmt_n(sh.get('xp', 0))}" + (f" · OČ {sh['oc']}" if sh.get("oc") is not None else ""),
                    size=13),
        ]
        attrs = sh.get("attrs") or []
        if attrs:
            body.append(ft.Row([k.stat(a, v) for a, v in zip(r.ATTRS, attrs)], spacing=6))
        items = sh.get("items") or []
        if items:
            body.append(k.text("Batoh", size=15, weight=ft.FontWeight.BOLD, head=True))
            body += [k.muted(f"• {i.get('name')}" + (f" ×{i['qty']}" if i.get("qty", 1) != 1 else "")
                             + (" (na těle)" if i.get("equipped") else ""), size=13) for i in items[:40]]
        money = sh.get("money") or {}
        if money:
            body.append(k.muted("Peníze: " + ", ".join(f"{v} {kk}" for kk, v in money.items()), size=13))
        app.page.show_dialog(ft.AlertDialog(
            title=k.text(sh.get("name", "Deník"), size=20, weight=ft.FontWeight.BOLD, head=True),
            content=ft.Container(ft.Column(body, spacing=6, tight=True, scroll=ft.ScrollMode.AUTO), width=360),
            actions=[ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())], bgcolor=l.card))
    app.run(run())


# --- úprava hráče (životy, zkušenosti, předmět) ------------------------------------------------------

def queue(app, camp, op: dict) -> None:
    """Akce PJ: hody jdou hned do hodů družiny, úpravy hráčů čekají ve frontě (server je zatím neumí)."""
    if op.get("op") == "roll":
        camp.setdefault("feed", []).insert(0, {"who": op["who"], "label": op["label"], "result": op["result"],
                                               "hidden": op.get("hidden", False), "created_at": time.time()})
        if camp.get("sid"):
            async def send():
                try:
                    await app.sync.gm_roll(camp, f"{op['who']}: {op['label']}", op["result"], op.get("hidden", False))
                except Exception:  # pragma: no cover - síť
                    pass
            app.run(send())
        app.save_gm(camp)
        return
    camp.setdefault("outbox", []).append(op)
    app.save_gm(camp)


def edit_player(app, camp, m) -> None:
    k = app.kit
    l = app.look
    s = m.get("snapshot") or {}
    sh = (camp.get("sheets") or {}).get(m.get("user_id")) or {}
    hp0, hpm = gm_view_hp(camp, m)
    hp0 = int(hp0 or 0)
    hpm = int(hpm or max(hp0, 1))
    st = {"hp": hp0, "xp": 0, "items": []}
    reason = k.field("Důvod (uvidí hráč)", "")
    holder = ft.Column(spacing=12, tight=True)

    def xp_sub() -> str:
        xp = sh.get("xp", s.get("xp"))
        if xp is None:
            return "zkušenosti se přičtou"
        new = int(xp) + st["xp"]
        nxt = sh.get("xp_next")
        lvl = sh.get("level", s.get("level"))
        tail = f" · do {int(lvl) + 1}. úr. chybí {fmt_n(max(0, int(nxt) - new))}" if nxt and lvl else ""
        return f"{fmt_n(xp)} → {fmt_n(new)}{tail}"

    def change(key, d):
        def h(e):
            st[key] += d
            draw()
        return h

    def add_item(e):
        def save(v):
            if str(v.get("name", "")).strip():
                st["items"].append({"name": v["name"].strip(), "qty": max(1, int(v.get("qty") or 1)),
                                    "weight": float(v.get("weight") or 0), "category": v.get("category") or "Ostatní"})
            app.page.show_dialog(dlg)
            draw()
        app.close_dialog()
        app.form("Předat předmět", [("name", "Předmět", "", "text"), ("qty", "Počet", 1, "int"),
                                    ("weight", "Váha", 0, "float"),
                                    ("category", "Druh", "Ostatní", "choice",
                                     ["Zbraň", "Zbroj", "Lektvar", "Svitek", "Ostatní"])], save, save_label="Přidat")

    def draw():
        d = st["hp"] - hp0
        quick = ft.Row([k.button(lbl, change("hp", v), primary=False, expand=1, height=40)
                        for lbl, v in (("−5", -5), ("−1", -1), ("+1", 1), ("+5", 5))], spacing=6)
        items = [k.muted("• " + i["name"] + (f" ×{i['qty']}" if i["qty"] != 1 else ""), size=13) for i in st["items"]]
        holder.controls = [
            ft.Row([k.avatar(initials(s.get("name")), 52),
                    ft.Column([k.text(s.get("name", "?"), size=21, weight=ft.FontWeight.BOLD, head=True),
                               k.muted(member_sub(sh or s), size=13)], spacing=2, expand=True),
                    k.pj_badge()], spacing=12),
            k.divider(),
            k.gauge("Životy", st["hp"], hpm, l.hp),
            quick,
            k.stepper(f"{hp0} → {st['hp']}", change("hp", -1), change("hp", 1), label="Nové životy",
                      sub=(f"změna {d:+d}" if d else "beze změny"), value_color=l.bad if d < 0 else (l.ok if d else None)),
            reason,
            k.divider(),
            k.stepper(f"{st['xp']:+d}", change("xp", -10), change("xp", 10), label="Zkušenosti", sub=xp_sub(),
                      value_color=l.ok if st["xp"] > 0 else None),
            k.button("Předat předmět do batohu", add_item, primary=False, icon=ft.Icons.BACKPACK_OUTLINED, height=44),
            *items,
            k.note("Změna se propíše do Deníku hráče, až bude propojení s hráči. Hráč uvidí upozornění.",
                   ft.Icons.NOTIFICATIONS_OUTLINED),
        ]
        try:
            app.page.update()
        except Exception:
            pass

    def save(e):
        payload: dict = {}
        if st["hp"] != hp0:
            payload["hp"] = st["hp"]
        if st["xp"]:
            payload["xp"] = st["xp"]
        if st["items"]:
            payload["items"] = st["items"]
        app.close_dialog()
        if not payload:
            return
        if (reason.value or "").strip():
            payload["reason"] = reason.value.strip()[:120]
        sh_ = camp.setdefault("sheets", {}).setdefault(m["user_id"], dict(sh or s))
        if "hp" in payload:
            sh_["hp"] = payload["hp"]
        if payload.get("xp"):
            sh_["xp"] = int(sh_.get("xp") or 0) + payload["xp"]
        queue(app, camp, {"op": "adjust", "uid": m["user_id"], "payload": payload})
        app.refresh()
        app.toast(f"Úprava pro {s.get('name', 'hráče')} uložena.")

    draw()
    dlg = ft.AlertDialog(
        content=ft.Container(ft.Column([holder], tight=True, scroll=ft.ScrollMode.AUTO), width=360),
        bgcolor=l.card, actions=[ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()),
                                 ft.FilledButton(content=ft.Text("Uložit"), on_click=save,
                                                 style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))])
    app.page.show_dialog(dlg)


# =============================================================================================== Souboj

def _combat(camp) -> dict | None:
    return camp.get("combat")


def _roll_ini(sysname: str) -> int:
    return random.randint(1, 6)


def start_combat(app, camp) -> None:
    order = []
    for m in players(camp):
        s = m.get("snapshot") or {}
        sh = (camp.get("sheets") or {}).get(m["user_id"]) or {}
        hp, hpm = gm_view_hp(camp, m)
        order.append({"id": model.new_id(), "kind": "player", "uid": m["user_id"], "name": s.get("name", "?"),
                      "ini": _roll_ini(camp["system"]), "hp": hp if hp is not None else 0, "hpm": hpm or 1,
                      "oc": sh.get("oc")})
    camp["combat"] = {"round": 1, "turn": 0, "order": sorted(order, key=lambda x: -x["ini"]), "target": None}
    app.save_gm(camp)


def add_monster(app, camp, b: dict) -> None:
    if not _combat(camp):
        start_combat(app, camp)
    c = camp["combat"]
    hp = int(b.get("hp", 0) or 0) or 10
    n = sum(1 for x in c["order"] if x.get("base") == b.get("name")) + 1
    name = b.get("name", "Nestvůra") + (f" {n}" if n > 1 else "")
    c["order"].append({"id": model.new_id(), "kind": "monster", "base": b.get("name"), "name": name,
                       "ini": _roll_ini(camp["system"]), "hp": hp, "hpm": hp, "uc": int(b.get("uc", 0) or 0),
                       "oc": int(b.get("oc", 0) or 0), "dmg": int(b.get("dmg", 0) or 0), "xp": int(b.get("xp", 0) or 0)})
    c["order"].sort(key=lambda x: -x["ini"])
    app.save_gm(camp)


def pj_souboj(app):
    from ..core import Screen

    camp = app.camp
    k = app.kit
    l = app.look
    c = _combat(camp)
    if not c:
        controls = [
            k.framed(ft.Column([k.text("Boj ještě nezačal", size=19, weight=ft.FontWeight.BOLD, head=True),
                                k.muted("Začni boj – hráči se zařadí do iniciativy, nestvůry přidáš z bestiáře. "
                                        "Jedna iniciativa pro hráče i nestvůry.", size=14)], spacing=6), glow=True),
            ft.Row([k.button("Začít boj", lambda e: (start_combat(app, camp), app.refresh()), icon=ft.Icons.SPORTS_MARTIAL_ARTS,
                             expand=1),
                    k.button("Nestvůra z bestiáře", lambda e: app.go("pj_bestiar"), primary=False, icon=ft.Icons.PETS_OUTLINED,
                             expand=1)], spacing=8),
            k.muted("Zásah hráče se mu hned odečte v jeho Deníku. Za poražené nestvůry nabídne aplikace zkušenosti.",
                    size=12),
        ]
        return Screen("Souboj", [column(controls)])
    order = c["order"]
    if order:
        c["turn"] %= len(order)
    cur = order[c["turn"]] if order else None

    def next_turn(e):
        if not order:
            return
        c["turn"] += 1
        if c["turn"] >= len(order):
            c["turn"] = 0
            c["round"] += 1
        app.save_gm(camp)
        app.refresh()

    def reroll(e):
        for x in order:
            x["ini"] = _roll_ini(camp["system"])
        order.sort(key=lambda x: -x["ini"])
        c["turn"] = 0
        app.save_gm(camp)
        app.refresh()

    rows = [_turn(app, camp, x, x is cur) for x in order]
    controls: list[ft.Control] = [
        ft.Row([k.text(f"Kolo {c['round']}", size=22, weight=ft.FontWeight.BOLD, head=True, expand=True),
                k.button("Další na tahu", next_turn, primary=False, icon=ft.Icons.CHEVRON_RIGHT, height=42)],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
        k.section("Iniciativa", icon=ft.Icons.HOURGLASS_EMPTY, trailing=k.link("Hodit znovu", reroll)),
        *(rows or [k.empty("V boji nikdo není.")]),
    ]
    if cur:
        controls.append(_act(app, camp, cur))
    controls += [
        ft.Row([k.button("Nestvůra z bestiáře", lambda e: app.go("pj_bestiar"), primary=False, icon=ft.Icons.PETS_OUTLINED,
                         expand=1, height=44),
                k.button("Ukončit boj", lambda e: end_combat(app, camp), primary=False, icon=ft.Icons.CLOSE, expand=1,
                         height=44)], spacing=8),
        k.muted("Zásah hráče se mu hned odečte v jeho Deníku. Za poražené nestvůry nabídne aplikace zkušenosti.", size=12),
    ]
    return Screen("Souboj", [column(controls)])


def _turn(app, camp, x, active) -> ft.Control:
    k = app.kit
    l = app.look
    monster = x["kind"] == "monster"
    tag = ft.Container(ft.Text("NESTVŮRA" if monster else "HRÁČ", size=10, weight=ft.FontWeight.BOLD,
                               color=l.bad if monster else l.orn),
                       border=ft.Border.all(1, l.bad if monster else l.frame), border_radius=ft.BorderRadius.all(4),
                       padding=ft.Padding.symmetric(horizontal=6, vertical=2))

    def tap(e):
        if monster:
            _monster_hp(app, camp, x)
        else:
            m = next((m for m in camp.get("members") or [] if m.get("user_id") == x.get("uid")), None)
            if m:
                edit_player(app, camp, m)
    body = ft.Row([
        ft.Container(k.text(str(x["ini"]), size=15, weight=ft.FontWeight.BOLD, head=True), width=34, height=34,
                     alignment=ft.Alignment.CENTER, bgcolor=l.bg, border=ft.Border.all(1, l.frame),
                     border_radius=ft.BorderRadius.all(l.radius)),
        ft.Column([ft.Row([k.text(x["name"], size=15, weight=ft.FontWeight.BOLD, max_lines=1), tag], spacing=6),
                   k.bar(max(0, x["hp"]), max(1, x["hpm"]), l.hp, l.hp_dark, height=10)], spacing=4, expand=True),
        k.text(f"{x['hp']}/{x['hpm']}", size=14, weight=ft.FontWeight.BOLD, head=True),
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Container(body, padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                        border_radius=ft.BorderRadius.all(l.radius),
                        gradient=k.grad(l.card2, l.card) if active else None, bgcolor=None if active else l.card,
                        border=ft.Border.all(1, l.orn if active else l.border), shadow=k.glow(14) if active else None,
                        opacity=0.5 if x["hp"] <= 0 else 1.0, on_click=tap, ink=True)


def _act(app, camp, cur) -> ft.Control:
    k = app.kit
    l = app.look
    c = camp["combat"]
    if cur["kind"] != "monster":
        return k.framed(ft.Column([
            ft.Row([ft.Icon(ft.Icons.SPORTS_MARTIAL_ARTS, size=20, color=l.orn),
                    k.text(f"Na tahu: {cur['name']}", size=17, weight=ft.FontWeight.BOLD, head=True)], spacing=8),
            k.muted("Hráč hází ve svém telefonu (Kostky → Souboj). Zásah od nestvůry zapíšeš klepnutím na hráče.", size=13),
        ], spacing=8), glow=True)
    targets = [x for x in c["order"] if x["kind"] == "player" and x["hp"] > 0]
    names = [x["name"].split()[0] for x in targets]
    tgt = next((x for x in targets if x["id"] == c.get("target")), targets[0] if targets else None)

    def pick(v):
        t = next((x for x in targets if x["name"].split()[0] == v), None)
        c["target"] = t["id"] if t else None
        app.refresh()

    stats = (f"ÚČ {cur['uc']} · OČ {cur['oc']} · Útočnost {fmt(cur['dmg'])}" if camp["system"] == "drd"
             else f"ÚČ {cur['uc']} · OČ {cur['oc']} · Zranění {cur['dmg']}")
    return k.framed(ft.Column([
        ft.Row([ft.Icon(ft.Icons.SPORTS_MARTIAL_ARTS, size=20, color=l.orn),
                k.text(f"Na tahu: {cur['name']}", size=17, weight=ft.FontWeight.BOLD, head=True)], spacing=8),
        k.muted(stats + (" · cíl:" if targets else " · žádný cíl"), size=13),
        k.pills(names, tgt["name"].split()[0] if tgt else "", pick) if names else ft.Container(),
        ft.Row([k.button("Útok", lambda e: attack(app, camp, cur, tgt, hidden=False), icon=ft.Icons.SPORTS_MARTIAL_ARTS,
                         expand=1, disabled=tgt is None),
                k.button("Skrytý hod", lambda e: attack(app, camp, cur, tgt, hidden=True), primary=False,
                         icon=ft.Icons.VISIBILITY_OFF_OUTLINED, expand=1, disabled=tgt is None)], spacing=8),
    ], spacing=10), glow=True)


def attack(app, camp, mon, tgt, hidden: bool) -> None:
    if tgt is None:
        return
    k = app.kit
    l = app.look
    rolls = drd.combat_roll() if camp["system"] == "drd" else dh.combat_roll(app.settings.get("dh_exploding", True))
    roll = sum(rolls)
    total = mon["uc"] + roll
    r = drd if camp["system"] == "drd" else dh
    oc = tgt.get("oc")
    dmg = r.wound(total, int(oc), mon["dmg"]) if oc is not None else max(0, mon["dmg"])
    st = {"dmg": dmg}
    queue(app, camp, {"op": "roll", "who": mon["name"], "label": f"Útok na {tgt['name']}", "result": str(total),
                      "hidden": hidden})
    label = k.text("", size=28, weight=ft.FontWeight.BOLD, head=True, color=l.bad, align=ft.TextAlign.CENTER)

    def draw():
        label.value = f"−{st['dmg']} životů"
        try:
            app.page.update()
        except Exception:
            pass

    def ch(d):
        def h(e):
            st["dmg"] = max(0, st["dmg"] + d)
            draw()
        return h

    def apply(e):
        app.close_dialog()
        if st["dmg"] > 0:
            tgt["hp"] -= st["dmg"]
            queue(app, camp, {"op": "adjust", "uid": tgt["uid"],
                              "payload": {"hp_delta": -st["dmg"], "reason": f"zásah: {mon['name']}"}})
        app.refresh()

    draw()
    detail = f"ÚČ {mon['uc']} + hod {'+'.join(str(x) for x in rolls)} = {total}" + \
             (f" proti OČ {oc}" if oc is not None else " (OČ hráče neznám – uprav zásah)")
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(f"{mon['name']} → {tgt['name']}" + (" (skrytě)" if hidden else ""), size=18,
                     weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column([k.muted(detail, size=14), label,
                                        ft.Row([k.square_button(ft.Icons.REMOVE, ch(-1), "Méně"),
                                                k.square_button(ft.Icons.ADD, ch(1), "Více")],
                                               alignment=ft.MainAxisAlignment.CENTER),
                                        k.muted("Obranný hod hráče aplikace nezná – zásah uprav podle něj.", size=12)],
                                       spacing=10, tight=True), width=340),
        actions=[ft.TextButton("Minul", on_click=lambda e: app.close_dialog()),
                 ft.FilledButton(content=ft.Text("Zapsat zásah"), on_click=apply,
                                 style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))]))


def _monster_hp(app, camp, x) -> None:
    def save(v):
        x["hp"] = int(v.get("hp") or 0)
        app.save_gm(camp)
        app.refresh()

    async def remove():
        camp["combat"]["order"] = [o for o in camp["combat"]["order"] if o["id"] != x["id"]]
        app.save_gm(camp)
        app.refresh()
    app.form(x["name"], [("hp", f"Životy (max {x['hpm']})", x["hp"], "int")], save, on_delete=remove)


def end_combat(app, camp) -> None:
    c = camp.get("combat") or {}
    beaten = [x for x in c.get("order", []) if x["kind"] == "monster" and x["hp"] <= 0]
    for x in beaten:
        camp.setdefault("xp_pool", []).append({"name": x["name"], "sub": "poražen", "xp": x.get("xp", 0)})
    camp["combat"] = None
    app.save_gm(camp)
    app.go("pj_nastroje" if beaten else "pj_souboj")
    app.toast("Boj skončil." + (" Zkušenosti za poražené nestvůry čekají v Nástrojích." if beaten else ""))


# =============================================================================================== Bestiář PJ

def pj_bestiar(app):
    from ..core import Screen

    camp = app.camp
    k = app.kit
    l = app.look
    sysk = camp["system"]
    src = app.ui.get("pjb_src", "Z pravidel PJ")
    size = app.ui.get("pjb_size", "Vše")
    q = app.ui.get("pjb_q", "")
    rules = list((app.pj_content.get("bestiar") or {}).get(sysk) or [])
    mine = app.bestiary.get(sysk, [])
    items = rules if src == "Z pravidel PJ" else mine
    from .kit import matches
    shown = [b for b in items if matches(q, b.get("name"), b.get("kind"))
             and (size == "Vše" or str(b.get("size", "")).upper().startswith(size))]

    def set_ui(key):
        def h(v):
            app.ui[key] = v
            app.refresh()
        return h

    controls: list[ft.Control] = [
        k.note("Obsah příruček Pána jeskyně. Je jen v telefonu PJ (nahraný balíček) – v aplikaci hráče ani "
               "v repozitáři není."),
        k.search(q, set_ui("pjb_q"), "Hledat nestvůru…"),
        k.pills(["Z pravidel PJ", "Moje nestvůry"], src, set_ui("pjb_src"), wrap=False),
    ]
    if sysk == "drd":
        controls.append(k.pills(["Vše", "A", "B", "C", "D", "E"], size, set_ui("pjb_size")))
    if shown:
        controls.append(k.list_card([_beast_row(app, camp, b, src) for b in shown]))
    elif src == "Z pravidel PJ" and not rules:
        controls.append(k.framed(ft.Column([
            k.text("Příručky PJ zatím nejsou nahrané", size=17, weight=ft.FontWeight.BOLD, head=True),
            k.muted("Nestvůry z pravidel PJ se načtou z balíčku (soubor .json), který dostaneš zvlášť. Zůstane jen "
                    "v tomto telefonu. Vlastní nestvůry si přidáš tlačítkem +.", size=14),
            k.button("Nahrát balíček PJ", lambda e: app.run(import_package(app)), primary=False,
                     icon=ft.Icons.UPLOAD_FILE, height=44),
        ], spacing=8)))
    else:
        controls.append(k.empty("Nic nenalezeno." if q or size != "Vše" else "Zatím žádné nestvůry. Přidej první +."))
    controls.append(ft.Container(height=70))
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=l.accent, foreground_color=l.on_accent,
                                  tooltip="Nová nestvůra", on_click=lambda e: edit_beast(app, camp, None))
    return Screen("Bestiář PJ", [column(controls)], fab=fab)


def _beast_row(app, camp, b, src) -> ft.Control:
    k = app.kit
    l = app.look
    if camp["system"] == "drd":
        sub = f"Životaschopnost {b.get('zvt', '?')} · ÚČ {b.get('uc', 0)} · OČ {b.get('oc', 0)} · velikost {b.get('size') or '?'}"
    else:
        sub = f"Životy {b.get('hp', 0)} · ÚČ {b.get('uc', 0)} · OČ {b.get('oc', 0)} · zranění {b.get('dmg', 0)}"
    right = b.get("src") or ("PJ" if src == "Z pravidel PJ" else "")
    return ft.Container(ft.Row([
        ft.Icon(ft.Icons.PETS_OUTLINED, size=22, color=l.orn),
        ft.Column([k.text(b.get("name", "?"), size=16, weight=ft.FontWeight.BOLD, max_lines=1),
                   k.muted(sub, size=13, max_lines=2)], spacing=2, expand=True),
        k.badge(right) if right else ft.Container(),
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: _beast_detail(app, camp, b, src),
        ink=True)


def _beast_detail(app, camp, b, src) -> None:
    k = app.kit
    fields = DH_FIELDS if camp["system"] == "dh" else DRD_FIELDS
    pairs = [(lbl, b.get(key)) for key, lbl, kind in fields[1:] if kind != "long" and b.get(key) not in (None, "")]
    body: list[ft.Control] = [ft.Row([k.muted(lbl, expand=True), k.text(val, size=14, weight=ft.FontWeight.W_600)])
                              for lbl, val in pairs]
    if b.get("note"):
        body.append(k.muted(b["note"], size=14))

    def fight(e):
        app.close_dialog()
        add_monster(app, camp, b)
        app.go("pj_souboj")

    acts = [ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]
    if src != "Z pravidel PJ":
        acts.insert(0, ft.TextButton("Upravit", on_click=lambda e: (app.close_dialog(), edit_beast(app, camp, b))))
    acts.append(ft.FilledButton(content=ft.Text("Do souboje"), on_click=fight,
                                style=ft.ButtonStyle(bgcolor=app.look.accent, color=app.look.on_accent)))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(b.get("name", "Nestvůra"), size=20, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
        content=ft.Container(ft.Column(body, spacing=6, tight=True, scroll=ft.ScrollMode.AUTO), width=340),
        actions=acts))


def edit_beast(app, camp, b) -> None:
    sysk = camp["system"]
    fields = DH_FIELDS if sysk == "dh" else DRD_FIELDS
    form = [(key, lbl, (b or {}).get(key, 0 if kind == "int" else ""), kind) for key, lbl, kind in fields]

    def save(v):
        if not str(v["name"]).strip():
            app.toast("Vyplň jméno nestvůry.")
            return
        if b is None:
            v["id"] = model.new_id()
            app.bestiary[sysk].insert(0, v)
        else:
            b.update(v)
        app.ui["pjb_src"] = "Moje nestvůry"
        app.save(bestiary=sysk)
        app.refresh()

    async def delete():
        app.bestiary[sysk] = [x for x in app.bestiary[sysk] if x is not b]
        app.save(bestiary=sysk)
        app.refresh()
    app.form("Nová nestvůra" if b is None else "Upravit nestvůru", form, save, on_delete=delete if b else None)


async def import_package(app) -> None:
    """Balíček příruček PJ (JSON) – zůstane jen v tomto zařízení."""
    files = await app.picker.pick_files(dialog_title="Balíček příruček PJ", allowed_extensions=["json"],
                                        file_type=ft.FilePickerFileType.CUSTOM, with_data=True)
    if not files:
        return
    f = files[0]
    data = getattr(f, "bytes", None)
    if not data and getattr(f, "path", None):
        with open(f.path, "rb") as fh:
            data = fh.read()
    try:
        pkg = json.loads(data.decode("utf-8"))
        assert isinstance(pkg, dict) and isinstance(pkg.get("bestiar", {}), dict)
    except Exception:
        info(app, "Balíček nejde načíst", "Soubor není balíček příruček PJ (JSON s oddílem „bestiar“).")
        return
    app.pj_content = pkg
    await app.store.set_json("pj_content", pkg)
    n = sum(len(v) for v in (pkg.get("bestiar") or {}).values())
    app.refresh()
    app.toast(f"Balíček nahrán: {n} nestvůr.")


# =============================================================================================== Nástroje

def pj_nastroje(app):
    from ..core import Screen

    camp = app.camp
    k = app.kit
    l = app.look

    def tile(icon, name, sub, phase, on_click=None):
        return ft.Container(ft.Column([
            ft.Icon(icon, size=26, color=l.orn),
            k.text(name, size=15, weight=ft.FontWeight.BOLD, head=True),
            k.muted(sub, size=12),
            k.text(phase, size=10, weight=ft.FontWeight.BOLD, color=l.orn),
        ], spacing=6), padding=ft.Padding.all(14), height=132, expand=1, border_radius=ft.BorderRadius.all(l.radius),
            gradient=k.grad(l.card2, l.card), border=ft.Border.all(1, l.frame),
            on_click=on_click or (lambda e, n=name: app.toast(f"{n}: připravujeme – fáze {PHASES.get(n, 8)} plánu "
                                                             "doplnění z příruček PJ.")), ink=True)
    tiles = [("STAR_OUTLINE", "Zkušenosti", "za nestvůry a úkoly, rozdělení družině", "FÁZE 8", lambda e: add_xp(app, camp)),
             ("HOURGLASS_EMPTY", "Čas a směny", "hodiny hry, trvání kouzel", "FÁZE 8", None),
             ("WB_SUNNY_OUTLINED", "Počasí a cesta", "podnebí, únava, bloudění", "FÁZE 6", None),
             ("GPS_FIXED", "Pasti", "nebezpečnost a hod pro hráče", "FÁZE 8", None),
             ("DIAMOND_OUTLINED", "Poklady", "generátor, rozdělení do batohů", "FÁZE 8", None),
             ("CASTLE_OUTLINED", "Panství a armády", "daně, hrady, bitvy", "FÁZE 9", None)]
    grid = [ft.Row([tile(getattr(ft.Icons, a[0]), *a[1:]) for a in tiles[i:i + 2]], spacing=8)
            for i in range(0, len(tiles), 2)]
    pool = camp.get("xp_pool") or []
    pl = players(camp)
    total = sum(int(x.get("xp", 0) or 0) for x in pool)
    each = total // len(pl) if pl else 0

    def share(e):
        if not pl or not total:
            app.toast("Není co rozdělit." if pl else "V kampani zatím nejsou hráči.")
            return
        for m in pl:
            camp.setdefault("outbox", []).append({"op": "adjust", "uid": m["user_id"],
                                                  "payload": {"xp": each, "reason": "zkušenosti za boj"}})
        camp["xp_pool"] = []
        app.save_gm(camp)
        app.refresh()
        app.toast(f"Každý hráč dostal {each} zk.")

    rows = [k.row_item(x["name"], str(x.get("xp", 0)), sub=x.get("sub")) for x in pool]
    xp_card = k.framed(ft.Column([
        ft.Row([ft.Icon(ft.Icons.STAR_OUTLINE, size=20, color=l.orn),
                k.text("Zkušenosti za boj", size=17, weight=ft.FontWeight.BOLD, head=True, expand=True),
                k.link("Přidat", lambda e: add_xp(app, camp))], spacing=8),
        *(rows or [k.muted("Za poražené nestvůry se tu zkušenosti objeví po skončení boje. Úkol přidáš "
                           "tlačítkem Přidat.", size=13)]),
        ft.Row([k.text(f"Celkem {total} · na hráče", size=15, expand=True),
                k.text(str(each), size=22, weight=ft.FontWeight.BOLD, head=True, color=l.ok)]),
        ft.Row([k.button(f"Rozdělit všem {_count(len(pl))}" if pl else "Rozdělit", share, icon=ft.Icons.CHECK, expand=1,
                         disabled=not (pl and total))]),
    ], spacing=10), glow=True)
    return Screen("Nástroje PJ", [column([*grid, xp_card])])


def _count(n: int) -> str:
    return {1: "jednomu", 2: "dvěma", 3: "třem", 4: "čtyřem", 5: "pěti", 6: "šesti"}.get(n, str(n))


def add_xp(app, camp) -> None:
    def save(v):
        if int(v.get("xp") or 0) <= 0:
            return
        camp.setdefault("xp_pool", []).append({"name": (v.get("name") or "Úkol").strip(), "sub": "PJ",
                                               "xp": int(v["xp"])})
        app.save_gm(camp)
        app.refresh()
    app.form("Zkušenosti za úkol", [("name", "Za co (např. zachráněný kupec)", "Úkol: ", "text"),
                                    ("xp", "Zkušenosti celkem", 0, "int")], save, save_label="Přidat")


# =============================================================================================== Poznámky

def pj_poznamky(app):
    from ..core import Screen

    camp = app.camp
    k = app.kit
    l = app.look
    notes = camp.setdefault("notes", [])
    maps = camp.setdefault("maps", [])
    pl = players(camp)
    names = [(m.get("snapshot") or {}).get("name", "?") for m in pl]
    to = app.ui.get("msg_to") if app.ui.get("msg_to") in names else (names[0] if names else None)
    msg = k.field("Zpráva", app.ui.get("msg_text", ""), multiline=True)

    def note_card(n):
        head = [k.text(n.get("title") or "Poznámka", size=16, weight=ft.FontWeight.BOLD, head=True)]
        if n.get("pinned"):
            head.insert(0, ft.Icon(ft.Icons.PUSH_PIN_OUTLINED, size=18, color=l.orn))
        return k.framed(ft.Column([ft.Row(head, spacing=8), k.text(n.get("text", ""), size=14)], spacing=6),
                        padding=ft.Padding.symmetric(horizontal=14, vertical=12), on_click=lambda e: edit_note(app, camp, n))

    def pick_to(v):
        app.ui["msg_to"] = v
        app.ui["msg_text"] = msg.value or ""
        app.refresh()

    def send(e):
        body = (msg.value or "").strip()
        m = next((m for m in pl if (m.get("snapshot") or {}).get("name") == to), None)
        if not body or not m:
            app.toast("Napiš zprávu a vyber hráče.")
            return
        queue(app, camp, {"op": "message", "uid": m["user_id"], "body": body})
        app.ui["msg_text"] = ""
        app.refresh()
        app.toast(f"Zpráva pro {to} čeká na propojení.")

    map_rows = []
    for mp in maps:
        if mp.get("shared"):
            map_rows.append(k.row_item(mp["title"], sub=f"sdíleno v sezení {mp.get('session', camp['session'])}",
                                       badge="SDÍLENO"))
        else:
            map_rows.append(k.row_item(mp["title"], sub="připraveno · hráči zatím nevidí",
                                       trailing=k.button("Sdílet", lambda e, mp=mp: share_map(app, camp, mp), primary=False,
                                                         icon=ft.Icons.SEND_OUTLINED, height=38)))
    pinned = sorted(notes, key=lambda n: not n.get("pinned"))
    controls: list[ft.Control] = [
        k.note("Vše na této obrazovce vidíš jen ty. Hráči dostanou jen to, co jim pošleš nebo sdílíš."),
        k.section("Tajné poznámky", icon=ft.Icons.HISTORY_EDU_OUTLINED, trailing=k.link("Přidat", lambda e: edit_note(app, camp, None))),
        *([note_card(n) for n in pinned] or [k.empty("Zatím žádné poznámky.")]),
        k.section("Připravené mapy", icon=ft.Icons.IMAGE_OUTLINED, trailing=k.link("Nahrát", lambda e: app.run(upload_map(app, camp)))),
        k.list_card(map_rows) if map_rows else k.empty("Mapu nahraj předem – hráči ji uvidí, až ji sdílíš."),
        k.section("Tajná zpráva hráči", icon=ft.Icons.SEND_OUTLINED),
    ]
    if names:
        controls.append(k.framed(ft.Column([
            k.pills(names, to, pick_to), msg,
            ft.Row([k.button(f"Poslat jen {_dative(to)}", send, icon=ft.Icons.SEND_OUTLINED, expand=1)]),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)))
    else:
        controls.append(k.empty("Zprávu pošleš, až budou v kampani hráči."))
    return Screen("Poznámky PJ", [column(controls)])


def _dative(name: str | None) -> str:
    """Kira → Kiře, Mirka → Mirce, Elwin → Elwinovi (jen první slovo jména)."""
    n = (name or "").split()[0] if name else ""
    if len(n) < 2:
        return n
    if n.endswith("a"):
        stem, last = n[:-1], n[-2]
        if last == "r":
            return stem[:-1] + "ře"
        if last == "k":
            return stem[:-1] + "ce"
        if last in "gh":
            return stem[:-1] + "ze"
        if last in "dtn":
            return stem + "ě"
        return stem + "e"
    if n[-1].lower() in "eiyouáéíýůú":
        return n
    return n + "ovi"


def edit_note(app, camp, n) -> None:
    def save(v):
        data = {"title": (v.get("title") or "").strip() or "Poznámka", "text": v.get("text") or "",
                "pinned": bool(v.get("pinned"))}
        if n is None:
            camp["notes"].insert(0, {"id": model.new_id(), **data})
        else:
            n.update(data)
        camp["notes_dirty"] = True
        app.save_gm(camp)
        app.refresh()

    async def delete():
        camp["notes"] = [x for x in camp["notes"] if x is not n]
        camp["notes_dirty"] = True
        app.save_gm(camp)
        app.refresh()
    app.form("Nová poznámka" if n is None else "Upravit poznámku",
             [("title", "Nadpis", (n or {}).get("title", ""), "text"), ("text", "Text", (n or {}).get("text", ""), "long"),
              ("pinned", "Připnout nahoru", (n or {}).get("pinned", False), "bool")], save,
             on_delete=delete if n else None)


async def upload_map(app, camp) -> None:
    data = await app.pick_image(1600)
    if not data:
        return
    ref = await app.store.save_image(model.new_id(), data)
    app.images[ref] = data

    def titled(v):
        camp["maps"].insert(0, {"id": model.new_id(), "title": (v.get("title") or "Mapa").strip(), "ref": ref,
                                "shared": False})
        app.save_gm(camp)
        app.refresh()
    app.form("Připravená mapa", [("title", "Název (např. Krypta – 1. patro)", "", "text")], titled, save_label="Uložit")


def share_map(app, camp, mp) -> None:
    """Sdílení mapy družině: nahraje ji na server, hráčům se uloží do Deníku → Obrázky."""
    if not camp.get("sid"):
        app.toast("Nejdřív kampani získej kód pro hráče (Stůl PJ → Kampaň).")
        return

    async def run():
        data = app.images.get(mp["ref"]) or await app.store.load_image(mp["ref"])
        if not data:
            app.toast("Obrázek mapy se nepodařilo načíst.")
            return
        try:
            await app.sync.gm_share_image(camp, data, mp["title"])
        except (sync.SyncError, OSError) as ex:
            info(app, "Mapa se neodeslala", str(ex) or "Bez připojení k internetu.")
            return
        mp.update(shared=True, session=camp["session"])
        app.save_gm(camp)
        app.refresh()
        app.toast("Mapa odeslána družině – hráči ji najdou v Deníku → Obrázky.")
    app.run(run())
