"""Obrazovka Družina – připojení ke hře, členové, hody družiny, obrázky od PJ, sdílení.

Každá hra má svou Družinu ve svém vzhledu (DrD Fire, DH Ice); kampaň patří vždy k jedné hře.
Spojení se serverem obstarává app.sync (src/app/sync.py).
"""
from __future__ import annotations

import time

import flet as ft

from .. import sync
from ..rules import dh, drd
from .kit import column

SYS_NAME = {"dh": dh.NAME, "drd": drd.NAME}


def _ago(ts: float | None) -> str:
    if not ts:
        return ""
    s = max(0, int(time.time() - ts))
    if s < 60:
        return "právě teď"
    if s < 3600:
        return f"před {s // 60} min"
    if s < 86400:
        return f"před {s // 3600} h"
    return time.strftime("%d. %m.", time.localtime(ts))


def status_card(app, c: dict) -> ft.Control:
    """Malá karta na obrazovce Postava: stav družiny a vstup do ní."""
    k = app.kit
    l = app.look
    camp = sync.campaign(c)
    if camp:
        title = camp["name"]
        n = len(camp.get("members") or []) or 1
        sub = f"{'PJ' if camp['role'] == 'gm' else 'Hráč'} · sezení {camp['session']} · {n} v družině"
    else:
        title = "Nepřipojeno ke hře"
        sub = "Připoj se ke kampani kódem od PJ, nebo ji založ."
    return k.card(ft.Row([
        ft.Icon(ft.Icons.GROUPS_OUTLINED, size=26, color=l.hi),
        ft.Column([k.text(title, size=16, weight=ft.FontWeight.BOLD, max_lines=1), k.muted(sub, size=13)],
                  spacing=2, expand=True),
        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=l.orn),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER), on_click=lambda e: app.go("druzina"))


def druzina(app):
    from ..core import Screen

    c = app.char
    camp = sync.campaign(c)
    if camp and sync.is_remote(camp) and time.time() - camp.get("last_sync", 0) > 3 and not app.ui.get("_syncing"):
        _sync_now(app, c, quiet=True)
    controls = _campaign_view(app, c, camp) if camp else _join_view(app, c)
    return Screen("Družina", [column(controls)])


def _busy(app, text: str) -> None:
    k = app.kit
    app.page.show_dialog(ft.AlertDialog(
        modal=True, content=ft.Row([ft.ProgressRing(width=22, height=22, color=app.look.hi),
                                    k.text(text, size=15)], spacing=14, tight=True)))


def _remote(app, title: str, coro_factory, ok_msg=None) -> None:
    """Spustí operaci se serverem s točícím se kolečkem a srozumitelnou chybou."""
    async def run():
        _busy(app, title)
        try:
            await coro_factory()
        except ValueError as ex:
            app.close_dialog()
            app.toast(str(ex))
            return
        except sync.SyncError as ex:
            app.close_dialog()
            _info(app, "Nepovedlo se", str(ex))
            return
        except OSError:
            app.close_dialog()
            _info(app, "Bez připojení", "Server družiny není dostupný. Zkontroluj internet a zkus to znovu.")
            return
        app.close_dialog()
        app.save(app.char)
        app.start_sync_loop()
        app.refresh()
        if ok_msg:
            app.toast(ok_msg() if callable(ok_msg) else ok_msg)
    app.run(run())


def _sync_now(app, c: dict, quiet: bool = False) -> None:
    async def run():
        app.ui["_syncing"] = True
        try:
            changed = await app.sync.sync(c)
            await app.after_sync(c, changed)
        finally:
            app.ui["_syncing"] = False
        if not quiet:
            app.refresh()
    app.run(run())


# --- nepřipojená postava -------------------------------------------------------------------------

def _join_view(app, c: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    game = SYS_NAME[c["system"]]
    online = sync.configured()

    def join(e):
        def do(v):
            code = sync.normalize_code(v.get("code", ""))
            if code is None:
                app.toast("Kód má 6 znaků, např. K7P-42Q.")
                return
            if not online:
                _info(app, "Připojení není zapnuté",
                      "Aplikace nemá nastavený server pro družinu, připojit se zatím nedá.")
                return
            _remote(app, "Připojuji ke kampani…", lambda: app.sync.join(c, code),
                    lambda: f"Jsi v kampani {c['campaign']['name']}.")
        app.form("Připojit se ke kampani", [("code", "Kód od PJ (např. K7P-42Q)", "", "text")], do,
                 save_label="Připojit")

    def create(e):
        def do(v):
            if online:
                _remote(app, "Zakládám kampaň…", lambda: app.sync.create(c, v.get("name", "")),
                        lambda: f"Kampaň založena, kód {c['campaign']['code']}.")
            else:
                sync.create_campaign(c, v.get("name", ""))
                app.save(c)
                app.refresh()
        app.form(f"Nová kampaň – {game}", [("name", "Název kampaně", "", "text")], do, save_label="Založit")

    steps = [
        ("1", "PJ založí kampaň", "Dostane krátký kód (např. K7P-42Q), který pošle hráčům."),
        ("2", "Hráči zadají kód", f"Připojí se postavou pro {game}. Postava jiné hry se připojit nedá."),
        ("3", "Hrajete spolu", "Životy a hody vidí celá družina, PJ vidí celé deníky a sdílí mapy."),
    ]
    step_rows = [ft.Row([
        ft.Container(k.text(n, size=16, weight=ft.FontWeight.BOLD, head=True, color=l.on_accent), width=30, height=30,
                     alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(15),
                     gradient=k.grad(l.accent2, l.accent)),
        ft.Column([k.text(t, size=15, weight=ft.FontWeight.BOLD), k.muted(d, size=13)], spacing=1, expand=True),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START) for n, t, d in steps]

    return [
        k.card(ft.Column([
            ft.Row([ft.Icon(ft.Icons.GROUPS_OUTLINED, size=30, color=l.hi),
                    k.text("Hraj s družinou", size=20, weight=ft.FontWeight.BOLD, head=True)], spacing=10),
            k.muted(f"{c['name']} zatím hraje sám. Připoj se ke kampani {game}, nebo ji jako PJ založ.", size=14),
        ], spacing=8), accent=True),
        ft.Row([k.button("Připojit se", join, icon=ft.Icons.LOGIN, expand=1),
                k.button("Založit (PJ)", create, primary=False, icon=ft.Icons.ADD, expand=1)], spacing=8),
        k.section("Jak to funguje", icon=ft.Icons.HELP_OUTLINE),
        k.card(ft.Column(step_rows, spacing=14)),
        k.section("Co uvidí ostatní", icon=ft.Icons.VISIBILITY_OUTLINED),
        k.list_card([
            k.row_item("Ostatní hráči", sub="jméno, povolání, úroveň, životy a hody"),
            k.row_item("PJ", sub="celý deník postavy – vlastnosti, batoh; může házet skrytě a sdílet mapy"),
            k.row_item("Jen ty (a PJ)", sub="batoh; osobní poznámky v Deníku nevidí nikdo"),
        ]),
        _status_note(app, None, 0),
    ]


# --- postava v kampani -----------------------------------------------------------------------------

def _campaign_view(app, c: dict, camp: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    gm = camp["role"] == "gm"
    remote = sync.is_remote(camp)

    def show_code(e):
        _info(app, "Kód pro připojení",
              f"Pošli hráčům kód {camp['code']}. Zadají ho v Družině své postavy pro {SYS_NAME[camp['system']]}.",
              big=camp["code"])

    def session(d):
        def h(e):
            new = max(1, camp["session"] + d)
            if remote:
                _remote(app, "Ukládám…", lambda: app.sync.set_session(c, new))
            else:
                camp["session"] = new
                app.save(c)
                app.refresh()
        return h

    def toggle(key):
        def h(e):
            camp[key] = bool(e.control.value)
            app.save(c)
            if remote:
                _sync_now(app, c)
            else:
                app.refresh()
        return h

    def leave(e):
        def yes(ev):
            app.close_dialog()
            if remote:
                _remote(app, "Odcházím…", lambda: app.sync.leave(c), "Kampaň opuštěna. Postava zůstala v telefonu.")
            else:
                sync.leave(c)
                app.save(c)
                app.refresh()
        text = ("Kampaň se ukončí pro celou družinu. Všechny postavy zůstanou hráčům v telefonech." if gm and remote
                else "Postava ti zůstane i s celým deníkem. Do kampaně se můžeš vrátit znovu kódem.")
        app.page.show_dialog(ft.AlertDialog(
            title=k.text("Ukončit kampaň?" if gm and remote else "Opustit kampaň?", size=19,
                         weight=ft.FontWeight.BOLD, head=True),
            content=k.muted(text, size=14),
            actions=[ft.TextButton("Zrušit", on_click=lambda ev: app.close_dialog()),
                     ft.TextButton("Ukončit" if gm and remote else "Opustit", on_click=yes)]))

    def publish(e):
        name = camp["name"]
        sync.leave(c)
        _remote(app, "Zakládám kampaň na serveru…", lambda: app.sync.create(c, name),
                lambda: f"Kampaň je na serveru, nový kód {c['campaign']['code']}.")

    def share_image(e):
        async def run():
            data = await app.pick_image()
            if not data:
                return

            def titled(v):
                _remote(app, "Nahrávám obrázek…", lambda: app.sync.share_image(c, data, v.get("title", "")),
                        "Obrázek sdílen s družinou.")
            app.form("Sdílet obrázek", [("title", "Název (např. Mapa dolů – 1. patro)", "", "text")], titled,
                     save_label="Sdílet")
        app.run(run())

    head = k.card(ft.Column([
        ft.Row([k.text(camp["name"], size=21, weight=ft.FontWeight.BOLD, head=True, expand=True, max_lines=2),
                k.badge("PJ" if gm else "HRÁČ")], vertical_alignment=ft.CrossAxisAlignment.START),
        k.muted(f"Kampaň · {SYS_NAME[camp['system']]} · sezení {camp['session']}", size=14),
        k.divider(),
        ft.Row([ft.Column([k.muted("Kód pro připojení", size=12),
                           k.text(camp["code"], size=26, weight=ft.FontWeight.BOLD, head=True, color=l.hi)],
                          spacing=0, expand=True),
                k.button("Sdílet kód", show_code, primary=False, icon=ft.Icons.QR_CODE_2, height=44)],
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ], spacing=8), accent=True)

    controls: list[ft.Control] = [head, _status_note(app, camp, sync.pending(c))]
    if not remote and sync.configured():
        controls.append(k.card(ft.Column([
            k.muted("Tahle kampaň vznikla jen v tomto telefonu. Přenes ji na server, ať se k ní můžou "
                    "připojit ostatní (dostane nový kód).", size=13),
            k.button("Přenést na server", publish, icon=ft.Icons.CLOUD_UPLOAD_OUTLINED, height=44),
        ], spacing=8)))

    # --- členové
    controls.append(k.section(f"Družina {len(camp.get('members') or []) or ''}".strip(),
                              icon=ft.Icons.GROUPS_OUTLINED))
    controls.append(_members(app, c, camp, gm))

    # --- hody
    controls.append(k.section("Hody družiny", icon=ft.Icons.CASINO_OUTLINED,
                              trailing=ft.TextButton("Kostky", on_click=lambda e: app.go("kostky"))))
    controls.append(_feed(app, c, camp))
    controls.append(k.muted("Skryté hody PJ vidí ostatní jen jako „Skrytý hod – jen pro PJ“.", size=12))

    # --- obrázky
    controls.append(k.section("Sdílené obrázky", icon=ft.Icons.MAP_OUTLINED,
                              trailing=ft.TextButton("Sdílet", on_click=share_image) if gm and remote else None))
    imgs = camp.get("images") or []
    if imgs:
        controls.append(k.list_card([
            k.row_item(i.get("title") or "Obrázek", sub=("v Deníku · " if i["path"] in camp.get("saved_images", [])
                                                         else "stahuji… · ") + _ago(sync._parse_ts(i.get("created_at"))),
                       on_click=lambda e: app.go("denik"))
            for i in imgs]))
    else:
        controls.append(k.empty("Mapy a obrázky od PJ se tu objeví a samy se uloží do Deníku." if not gm else
                                "Klepni na Sdílet – obrázek uvidí celá družina a uloží se jim do Deníku."))

    # --- sdílení
    switches: list[ft.Control] = [
        ft.Switch(label="Sdílet moje hody s družinou", value=camp["share_rolls"], active_color=l.hi,
                  on_change=toggle("share_rolls")),
        ft.Switch(label="Sdílet moje životy s družinou", value=camp["share_hp"], active_color=l.hi,
                  on_change=toggle("share_hp")),
    ]
    if gm:
        switches.append(ft.Switch(label="Moje hody jsou skryté (jen pro PJ)", value=camp.get("hide_rolls", False),
                                  active_color=l.hi, on_change=toggle("hide_rolls")))
    switches.append(k.muted("Batoh vidí jen PJ. Osobní poznámky v Deníku se nesdílí.", size=12))
    controls += [k.section("Sdílení", icon=ft.Icons.TUNE), k.card(ft.Column(switches, spacing=4))]

    if gm:
        controls += [k.section("Pro PJ", icon=ft.Icons.SHIELD_OUTLINED),
                     k.card(k.stepper(camp["session"], session(-1), session(+1), label="Sezení",
                                      sub="+1 na začátku každého hraní"))]
    controls.append(ft.Row([k.button("Ukončit kampaň" if gm and remote else "Opustit kampaň", leave, primary=False,
                                     icon=ft.Icons.LOGOUT, expand=1)]))
    return controls


def _members(app, c: dict, camp: dict, gm: bool) -> ft.Control:
    k = app.kit
    l = app.look
    me_uid = app.sync.uid if sync.configured() else None
    members = camp.get("members") or []
    if not members:  # bez serveru: jen já
        snap = sync.snapshot(c)
        members = [{"user_id": me_uid, "role": camp["role"], "snapshot": snap, "last_seen": time.time()}]
    rows: list[ft.Control] = []
    for m in members:
        s = m.get("snapshot") or {}
        me = m.get("user_id") == me_uid or len(members) == 1
        online = me or sync.is_online(m)
        badge = "PJ" if m.get("role") == "gm" else ("ONLINE" if online else "OFFLINE")
        sub = " · ".join(str(x) for x in (s.get("race"), s.get("cls"),
                                          f"{s.get('level')}. úroveň" if s.get("level") else None) if x)
        col: list[ft.Control] = [
            ft.Row([ft.Icon(ft.Icons.CIRCLE, size=10, color=l.ok if online else l.muted),
                    k.text(f"{s.get('name', '?')}{' (ty)' if me else ''}", size=16, weight=ft.FontWeight.BOLD,
                           expand=True, max_lines=1),
                    k.badge(badge)], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ]
        if sub:
            col.append(k.muted(sub, size=13))
        if s.get("hp") is not None and s.get("hp_max"):
            col.append(ft.Row([ft.Container(k.bar(s["hp"], s["hp_max"], l.hp, l.hp_dark, height=12), expand=True),
                               k.text(f"{s['hp']}/{s['hp_max']}", size=13, weight=ft.FontWeight.BOLD, head=True)],
                              spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER))
        elif m.get("role") != "gm":
            col.append(k.muted("životy nesdílí" if not me else "životy nesdílíš", size=12))
        if not online and not me:
            col.append(k.muted("offline · dorovná se po připojení", size=12))
        click = None
        if gm and not me and m.get("role") != "gm" and m.get("user_id"):
            click = (lambda e, m=m: _show_sheet(app, camp, m))
        rows.append(ft.Container(ft.Column(col, spacing=4), on_click=click, ink=click is not None))
    if len(members) == 1 and sync.is_remote(camp):
        rows.append(k.muted(f"Zatím jsi tu sám. Pošli ostatním kód {camp['code']}.", size=13))
    elif not sync.is_remote(camp):
        rows.append(k.muted("Ostatní členové se objeví, až bude kampaň na serveru.", size=13))
    return k.list_card(rows)


def _feed(app, c: dict, camp: dict) -> ft.Control:
    k = app.kit
    if sync.is_remote(camp):
        feed = camp.get("feed") or []
        rows = [k.row_item(f"{r['who']} · {r['label']}", r["result"],
                           sub=_ago(sync._parse_ts(r.get("created_at"))) + (" · skrytý" if r.get("hidden") else ""))
                for r in feed[:12]]
    else:
        rows = [k.row_item(f"{c['name']} · {h['label']}", h["value"], sub=_ago(h["ts"]))
                for h in (sync.rolls(c)[:8] if camp["share_rolls"] else [])]
    if rows:
        return k.list_card(rows)
    return k.empty("Zatím žádné hody." if camp["share_rolls"] else "Sdílení hodů máš vypnuté.")


def _show_sheet(app, camp: dict, m: dict) -> None:
    """Pohled PJ na deník hráče (jen čtení)."""
    k = app.kit
    l = app.look

    async def run():
        _busy(app, "Načítám deník…")
        try:
            sh = await app.sync.member_sheet(camp, m["user_id"])
        except (sync.SyncError, OSError) as ex:
            app.close_dialog()
            _info(app, "Nepovedlo se", str(ex) or "Bez připojení.")
            return
        app.close_dialog()
        if not sh:
            _info(app, "Deník", "Hráč zatím deník neposlal.")
            return
        r = drd if camp["system"] == "drd" else dh
        body: list[ft.Control] = [
            k.muted(" · ".join(str(x) for x in (sh.get("race"), sh.get("cls"), sh.get("branch"),
                                                f"{sh.get('level')}. úroveň") if x), size=14),
            k.text(f"Životy {sh.get('hp')}/{sh.get('hp_max')}" + (f" · {sh.get('mana_name') or 'Mana'} "
                                                                    f"{sh.get('mana')}/{sh.get('mana_max')}"
                                                                    if sh.get("mana_max") else ""), size=15,
                   weight=ft.FontWeight.BOLD),
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


def _status_note(app, camp: dict | None, pending: int) -> ft.Control:
    k = app.kit
    l = app.look
    btn = None
    if camp and sync.is_remote(camp):
        if camp.get("online"):
            txt = f"Propojeno se serverem · aktualizováno {_ago(camp.get('last_sync'))}."
            icon, color = ft.Icons.CLOUD_DONE_OUTLINED, l.ok
        else:
            txt = (camp.get("error") or "Offline.") + (f" {pending} hodů čeká na odeslání." if pending else "") + \
                  " Hraj dál, odešle se po připojení."
            icon, color = ft.Icons.CLOUD_OFF_OUTLINED, l.warn
        btn = ft.IconButton(ft.Icons.REFRESH, icon_color=l.orn, tooltip="Obnovit",
                            on_click=lambda e: _sync_now(app, app.char))
    elif sync.configured():
        txt = "Server družiny je připraven. Připojení potřebuje internet."
        icon, color = ft.Icons.CLOUD_QUEUE, l.ok
    else:
        txt = ("Offline – server pro družinu není nastavený. Vše funguje v tomto telefonu"
               + (f"; {pending} hodů čeká na odeslání." if pending else "."))
        icon, color = ft.Icons.CLOUD_OFF_OUTLINED, l.warn
    row: list[ft.Control] = [ft.Icon(icon, size=20, color=color), k.muted(txt, size=13, expand=True)]
    if btn:
        row.append(btn)
    return ft.Row(row, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _info(app, title: str, text: str, big: str | None = None) -> None:
    k = app.kit
    body: list[ft.Control] = []
    if big:
        body.append(ft.Container(k.text(big, size=40, weight=ft.FontWeight.BOLD, head=True, color=app.look.hi,
                                        align=ft.TextAlign.CENTER), alignment=ft.Alignment.CENTER,
                                 padding=ft.Padding.symmetric(vertical=10)))
    body.append(k.muted(text, size=14))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(title, size=19, weight=ft.FontWeight.BOLD, head=True),
        content=ft.Container(ft.Column(body, spacing=8, tight=True), width=340),
        actions=[ft.TextButton("Rozumím", on_click=lambda e: app.close_dialog())]))
