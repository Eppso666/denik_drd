"""Družina z pohledu hráče (podle grafického návrhu): připojení ke stolu nebo na server PJ, čekání na
schválení PJ a kampaň – úpravy od PJ, tajné zprávy, družina, hody a obrázky.

Každá hra má svou Družinu ve svém vzhledu (DrD Fire, DH Ice); kampaň patří vždy k jedné hře.
Hráč nevidí bestiář, poznámky ani nástroje PJ. Životy a zkušenosti mu může změnit jen PJ kampaně.
"""
from __future__ import annotations

import time

import flet as ft

from .. import stul, sync
from ..rules import dh, drd
from . import net
from .kit import column

SYS_NAME = {"dh": dh.NAME, "drd": drd.NAME}
_ago = net.ago


def status_card(app, c: dict) -> ft.Control:
    """Malá karta na obrazovce Postava: stav družiny a vstup do ní."""
    k = app.kit
    l = app.look
    camp = sync.campaign(c)
    if camp and sync.is_remote(camp):
        title = camp["name"]
        if camp.get("status") == "pending":
            sub = "Čekáš, až tě PJ přijme"
        else:
            n = len(sync.players(camp)) or 1
            sub = f"Hráč · sezení {camp['session']} · {n} v družině" + (" · U stolu" if sync.is_table(camp) else "")
    else:
        title = "Nepřipojeno ke hře"
        sub = "Připoj se ke stolu nebo pozvánkou od PJ."
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
    if camp and not sync.is_remote(camp):  # kampaň jen v telefonu ze starší verze – už nemá smysl
        sync.leave(c)
        app.save(c)
        camp = None
    if camp and time.time() - camp.get("last_sync", 0) > 3 and not app.ui.get("_syncing"):
        _sync_now(app, c, quiet=True)
    if not camp:
        return Screen("Připojit ke stolu", [column(_join_view(app, c))])
    if camp.get("status") == "pending":
        return Screen("Družina", [column(_waiting_view(app, c, camp))])
    return Screen("Družina", [column(_campaign_view(app, c, camp))])


def _sync_now(app, c: dict, quiet: bool = False) -> None:
    async def run():
        app.ui["_syncing"] = True
        try:
            camp = sync.campaign(c)
            res = await sync.sync_player(app.client(sync.server_of(camp)), c)
            await app.after_sync(c, res)
        finally:
            app.ui["_syncing"] = False
        if not quiet or res.get("changed"):
            app.refresh()
    app.run(run())


def _join(app, c: dict, srv: dict, code: str) -> None:
    cl = app.client(srv)

    async def do():
        row = await cl.join(code, c["system"], c["id"], sync.snapshot(c))
        c["campaign"] = sync.base_campaign(row.get("system", c["system"]), id=row["id"], name=row["name"],
                                           code=row.get("code", code), session=row.get("session", 1), role="player",
                                           status="pending", server=srv, uid=cl.uid)
        await sync.sync_player(cl, c)
        app.save(c)

    def done(_):
        app.ui.pop("join_sel", None)
        app.ui.pop("invite_text", None)
    net.remote(app, "Posílám žádost PJ…", do,
               lambda: ("Jsi v kampani." if (sync.campaign(c) or {}).get("status") == "approved"
                        else "Žádost odeslána – počkej, až tě PJ přijme."), after=done)


# --- nepřipojená postava: hledání stolu nebo pozvánka --------------------------------------------

def _search(app, code: str | None = None, then=None) -> None:
    async def run():
        app.ui.update(tables_busy=True, tables_err=None)
        app.refresh()
        try:
            found = await stul.find_tables()
        except stul.TableError as ex:
            found, app.ui["tables_err"] = [], str(ex)
        except Exception:  # pragma: no cover
            found, app.ui["tables_err"] = [], "Hledání se nepovedlo."
        app.ui.update(tables=found, tables_busy=False)
        if code is not None:
            hit = next((t for t in found if t.get("code") == code), None)
            if hit:
                app.ui["join_sel"] = hit
                app.ui["join_tab"] = "Hledat stůl"
            else:
                app.toast(f"Stůl {code} na této Wi-Fi nenalezen.")
        app.refresh()
    app.run(run())


def _join_view(app, c: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    u = app.ui
    web = not stul.supported()
    if u.get("invite_text") and not u.get("join_tab"):
        u["join_tab"] = "Zadat ručně"
    tab = u.get("join_tab") or ("Zadat ručně" if web else "Hledat stůl")

    def set_tab(v):
        u["join_tab"] = v
        app.refresh()

    controls: list[ft.Control] = [k.pills(["Hledat stůl", "Zadat ručně"], tab, set_tab, equal=True)]
    if tab == "Hledat stůl":
        if not web and u.get("tables") is None and not u.get("tables_busy"):
            _search(app)
        controls += _finder(app, c, web)
    else:
        controls += _manual(app, c)
    controls.append(k.note("Tip: nejste na stejné Wi-Fi? PJ může zapnout hotspot v telefonu – internet není potřeba."
                           if not web else stul.WEB_MSG, ft.Icons.WIFI))
    controls += [
        k.section("Co uvidí ostatní", icon=ft.Icons.VISIBILITY_OUTLINED),
        k.list_card([
            k.row_item("Ostatní hráči", sub="jméno, povolání, úroveň, životy a hody"),
            k.row_item("PJ", sub="celý deník postavy; smí ti měnit životy a zkušenosti a poslat předmět nebo zprávu"),
            k.row_item("Jen ty (a PJ)", sub="batoh; osobní poznámky v Deníku nevidí nikdo"),
        ]),
    ]
    return controls


def _finder(app, c: dict, web: bool) -> list[ft.Control]:
    k = app.kit
    l = app.look
    u = app.ui
    busy = u.get("tables_busy")
    found = u.get("tables") or []
    msg = (stul.WEB_MSG if web else "Hledám stoly na Wi-Fi…" if busy else u.get("tables_err") or
           (f"Nalezeno stolů: {len(found)}" if found else "Žádný stůl nenalezen. Má PJ otevřený Stůl PJ?"))
    box = ft.Container(
        ft.Stack([
            ft.Container(ft.Container(
                ft.ProgressRing(width=36, height=36, color=l.accent2) if busy else
                ft.Icon(ft.Icons.WIFI_FIND if not web else ft.Icons.WIFI_OFF, size=48, color=l.accent2),
                width=170, height=170, alignment=ft.Alignment.CENTER, border=ft.Border.all(3, l.accent2),
                border_radius=ft.BorderRadius.all(12), shadow=k.glow(18)), alignment=ft.Alignment.CENTER),
            ft.Container(k.text(msg, size=14, align=ft.TextAlign.CENTER), alignment=ft.Alignment.BOTTOM_CENTER,
                         padding=ft.Padding.only(bottom=12, left=12, right=12)),
        ], fit=ft.StackFit.EXPAND),
        height=260, border_radius=ft.BorderRadius.all(10),
        gradient=ft.RadialGradient(colors=["#24384f" if l.key == "dh" else "#3a2216", "#081426" if l.key == "dh" else "#120a07"]),
    )
    out: list[ft.Control] = [box]
    if not web:
        out.append(k.button("Hledat znovu", lambda e: _search(app), primary=False, icon=ft.Icons.REFRESH, height=44,
                            disabled=bool(busy)))
    sel = u.get("join_sel")
    if found:
        rows = []
        for t in found:
            sub = f"{SYS_NAME.get(t.get('system'), '?')} · STŮL {t.get('code')} · hráčů {t.get('players', 0)}"
            rows.append(k.row_item(t.get("name", "Stůl PJ"), sub=sub + (" · zamčeno" if t.get("locked") else ""),
                                   on_click=lambda e, t=t: (u.__setitem__("join_sel", t), app.refresh()),
                                   trailing=ft.Icon(ft.Icons.CHECK if sel and sel.get("host") == t.get("host")
                                                    else ft.Icons.CHEVRON_RIGHT, color=l.orn)))
        out.append(k.list_card(rows))
    if sel:
        same = sel.get("system") == c["system"]
        out.append(k.framed(ft.Column([
            k.check("Nalezen stůl PJ", sub=f"{sel.get('name')} · {SYS_NAME.get(sel.get('system'), '?')}"),
            k.check("Stejná hra jako tvoje postava" if same else "Jiná hra než tvoje postava", ok=same, bad=not same,
                    sub=f"{c['name']} · {c['race']} · {c['cls']}"),
            k.check("Čekáš, až tě PJ přijme", ok=False),
            k.button("Požádat o vstup", lambda e: _join(app, c, {"kind": "table", "host": sel["host"],
                                                                  "code": sel["code"], "name": sel.get("name")},
                                                         sel["code"]), icon=ft.Icons.LOGIN, disabled=not same),
        ], spacing=10)))
    return out


def _manual(app, c: dict) -> list[ft.Control]:
    k = app.kit
    u = app.ui
    fld = k.field("Pozvánka od PJ (odkaz) nebo kód stolu", u.get("invite_text", ""), multiline=False)

    def paste(e):
        async def run():
            try:
                fld.value = await ft.Clipboard().get() or ""
                u["invite_text"] = fld.value
                app.refresh()
            except Exception:
                app.toast("Schránka není dostupná – vlož odkaz ručně.")
        app.run(run())

    def go(e):
        text = (fld.value or "").strip()
        u["invite_text"] = text
        digits = "".join(ch for ch in text if ch.isdigit())
        inv = sync.parse_invite(text)
        if inv:
            _join(app, c, inv["server"], inv["code"])
        elif len(digits) == 4 and len(text.replace(" ", "").upper().replace("STŮL", "").replace("STUL", "")) == 4:
            if not stul.supported():
                net.info(app, "U stolu", stul.WEB_MSG)
                return
            _search(app, code=digits)
        elif sync.normalize_code(text) and sync.legacy_server():
            _join(app, c, sync.legacy_server(), sync.normalize_code(text))
        else:
            net.info(app, "Tohle nesedí", "Vlož celý odkaz pozvánky, který ti poslal PJ (začíná "
                                          f"{sync.INVITE_BASE}…), nebo čtyřmístný kód stolu.")
    return [
        k.framed(ft.Column([
            k.text("Pozvánka nebo kód stolu", size=17, weight=ft.FontWeight.BOLD, head=True),
            k.muted("Hraje se na serveru PJ? Vlož odkaz z pozvánky (nebo naskenuj QR fotoaparátem – otevře se "
                    "webová verze). Hraje se u stolu? Zadej kód stolu, např. 4821.", size=13),
            fld,
            ft.Row([k.button("Vložit ze schránky", paste, primary=False, icon=ft.Icons.CONTENT_PASTE, expand=1,
                             height=44),
                    k.button("Připojit", go, icon=ft.Icons.LOGIN, expand=1, height=44)], spacing=8),
        ], spacing=10)),
    ]


# --- čekání na schválení ---------------------------------------------------------------------------

def _waiting_view(app, c: dict, camp: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look

    def cancel(e):
        _leave(app, c, camp, "Žádost zrušena.")
    code = (f"stůl {camp['code']}" if sync.is_table(camp) else f"kód {camp.get('code')}")
    return [
        k.framed(ft.Column([
            ft.Icon(ft.Icons.HOURGLASS_TOP, size=40, color=l.accent2),
            k.text("Čekáš na PJ", size=21, weight=ft.FontWeight.BOLD, head=True),
            k.muted(f"Zadal jsi {code} kampaně {camp['name']}. Až tě PJ přijme, uvidíš družinu a hody.", size=14,
                    align=ft.TextAlign.CENTER),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=18, glow=True),
        k.list_card([k.row_item("Kampaň", sub=f"{camp['name']} · {SYS_NAME[camp['system']]}"),
                     k.row_item("Postava", sub=f"{c['name']} · {c['race']} · {c['cls']}")]),
        ft.Row([k.button("Zrušit žádost", cancel, primary=False, icon=ft.Icons.CLOSE, expand=1, height=46)]),
        _status_note(app, camp, 0),
        k.note("Kód sám nestačí – do kampaně pustí hráče jen PJ. Zamčená kampaň nové žádosti nepřijímá.",
               ft.Icons.SHIELD_OUTLINED),
    ]


def _leave(app, c: dict, camp: dict, msg: str) -> None:
    cl = app.client(sync.server_of(camp))

    async def do():
        try:
            await cl.leave(camp["id"])
        except (sync.SyncError, OSError):
            pass  # u stolu nebo offline – postava kampaň opustí i tak
        sync.leave(c)
        app.save(c)
    net.remote(app, "Odcházím…", do, msg)


# --- postava v kampani -----------------------------------------------------------------------------

def _campaign_view(app, c: dict, camp: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    controls: list[ft.Control] = []
    notice = camp.get("notice")
    if notice and time.time() - notice.get("ts", 0) < 6 * 3600:
        def dismiss(e):
            camp.pop("notice", None)
            app.save(c)
            app.refresh()
        controls.append(ft.Container(ft.Row([
            ft.Icon(ft.Icons.NOTIFICATIONS_OUTLINED, size=20, color=l.ptext),
            ft.Column([k.text("PJ ti upravil postavu", size=15, weight=ft.FontWeight.BOLD, color=l.ptext),
                       k.text(notice["text"], size=13, color=l.pmuted)], spacing=1, expand=True),
        ], spacing=10), padding=ft.Padding.symmetric(horizontal=14, vertical=12), bgcolor=l.parch,
            border=ft.Border.all(1, l.orn), border_radius=ft.BorderRadius.all(l.radius), shadow=k.glow(14),
            on_click=dismiss, ink=True, tooltip="Skrýt"))
    controls.append(k.framed(ft.Column([
        k.text(camp["name"], size=19, weight=ft.FontWeight.BOLD, head=True),
        k.muted(f"{SYS_NAME[camp['system']]} · sezení {camp['session']} · jsi hráč"
                + (" · u stolu" if sync.is_table(camp) else ""), size=13),
    ], spacing=4), padding=ft.Padding.symmetric(horizontal=14, vertical=12)))
    msgs = camp.get("messages") or []
    if msgs:
        m = msgs[0]
        more = (k.link(f"Starší zprávy ({len(msgs) - 1})", lambda e: _old_messages(app, msgs))
                if len(msgs) > 1 else ft.Container())
        controls.append(k.framed(ft.Column([
            ft.Row([ft.Icon(ft.Icons.MAIL_OUTLINE, size=18, color=l.orn),
                    k.text("Zpráva jen pro tebe", size=16, weight=ft.FontWeight.BOLD, head=True, expand=True), more],
                   spacing=8),
            k.text(m.get("body", ""), size=14),
            k.muted(f"od PJ · {net.ago(m.get('created_at'))}", size=12),
        ], spacing=6), padding=ft.Padding.symmetric(horizontal=14, vertical=12), glow=True))

    controls.append(k.section("Družina", icon=ft.Icons.GROUPS_OUTLINED))
    controls.append(_members(app, c, camp))
    controls.append(k.section("Hody družiny", icon=ft.Icons.CASINO_OUTLINED,
                              trailing=k.link("Kostky", lambda e: app.go("kostky"))))
    controls.append(_feed(app, c, camp))
    controls.append(k.note("Hráč nevidí bestiář, poznámky ani nástroje PJ. Životy a zkušenosti mu může změnit jen PJ "
                           "kampaně.", ft.Icons.SHIELD_OUTLINED))

    imgs = camp.get("images") or []
    controls.append(k.section("Obrázky od PJ", icon=ft.Icons.MAP_OUTLINED))
    if imgs:
        controls.append(k.list_card([
            k.row_item(i.get("title") or "Obrázek", sub=("v Deníku · " if i["path"] in camp.get("saved_images", [])
                                                         else "stahuji… · ") + net.ago(i.get("created_at")),
                       on_click=lambda e: app.go("denik"))
            for i in imgs]))
    else:
        controls.append(k.empty("Mapy a obrázky od PJ se tu objeví a samy se uloží do Deníku."))

    def toggle(key):
        def h(e):
            camp[key] = bool(e.control.value)
            app.save(c)
            _sync_now(app, c)
        return h
    controls += [k.section("Sdílení", icon=ft.Icons.TUNE), k.card(ft.Column([
        ft.Switch(label="Sdílet moje hody s družinou", value=camp["share_rolls"], active_color=l.hi,
                  on_change=toggle("share_rolls")),
        ft.Switch(label="Sdílet moje životy s družinou", value=camp["share_hp"], active_color=l.hi,
                  on_change=toggle("share_hp")),
        k.muted("PJ vidí celý deník vždy. Osobní poznámky v Deníku se nesdílí.", size=12),
    ], spacing=4))]
    controls.append(_status_note(app, camp, sync.pending(c)))

    def leave(e):
        def yes(ev):
            app.close_dialog()
            _leave(app, c, camp, "Kampaň opuštěna. Postava zůstala v telefonu.")
        app.page.show_dialog(ft.AlertDialog(
            title=k.text("Opustit kampaň?", size=19, weight=ft.FontWeight.BOLD, head=True),
            content=k.muted("Postava ti zůstane i s celým deníkem. Vrátit se můžeš, PJ tě ale musí znovu přijmout.",
                            size=14),
            actions=[ft.TextButton("Zrušit", on_click=lambda ev: app.close_dialog()),
                     ft.TextButton("Opustit", on_click=yes)]))
    controls.append(ft.Row([k.button("Opustit kampaň", leave, primary=False, icon=ft.Icons.LOGOUT, expand=1)]))
    return controls


def _old_messages(app, msgs: list[dict]) -> None:
    net.info(app, "Zprávy od PJ", "\n\n".join(f"{m.get('body')}\n({net.ago(m.get('created_at'))})" for m in msgs))


def _members(app, c: dict, camp: dict) -> ft.Control:
    k = app.kit
    me_uid = camp.get("uid") or app.client(sync.server_of(camp)).uid
    members = [m for m in camp.get("members") or [] if m.get("status", "approved") == "approved"]
    if not members:
        members = [{"user_id": me_uid, "role": "player", "snapshot": sync.snapshot(c), "last_seen": time.time()}]
    rows: list[ft.Control] = []
    for m in sorted(members, key=lambda m: m.get("role") == "gm"):
        s = m.get("snapshot") or {}
        if m.get("role") == "gm":
            rows.append(k.row_item(s.get("name") or sync.GM_NAME, sub="Pán jeskyně", badge="PJ"))
            continue
        me = m.get("user_id") == me_uid
        online = me or sync.is_online(m)
        sub = net.member_sub(s) + ("" if online else " · offline")
        hp = f"{s['hp']}/{s['hp_max']}" if s.get("hp") is not None and s.get("hp_max") else ""
        rows.append(k.row_item(f"{s.get('name', '?')}{' (ty)' if me else ''}", hp, sub=sub or None))
    return k.list_card(rows)


def _feed(app, c: dict, camp: dict) -> ft.Control:
    k = app.kit
    feed = camp.get("feed") or []
    rows = [k.row_item(f"{r['who']} · {r['label']}", "?" if r.get("hidden") and r["result"] == "jen pro PJ" else r["result"],
                       sub=("jen pro PJ" if r.get("hidden") else net.ago(r.get("created_at"))))
            for r in feed[:12]]
    if rows:
        return k.list_card(rows)
    return k.empty("Zatím žádné hody." if camp["share_rolls"] else "Sdílení hodů máš vypnuté.")


def _status_note(app, camp: dict | None, pending: int) -> ft.Control:
    k = app.kit
    l = app.look
    btn = None
    if camp:
        where = "se stolem PJ" if sync.is_table(camp) else "se serverem PJ"
        if camp.get("online"):
            txt = f"Propojeno {where} · aktualizováno {net.ago(camp.get('last_sync'))}."
            icon, color = ft.Icons.CLOUD_DONE_OUTLINED, l.ok
        else:
            txt = (camp.get("error") or "Offline.") + (f" {pending} hodů čeká na odeslání." if pending else "") + \
                  " Hraj dál, odešle se po připojení."
            icon, color = ft.Icons.CLOUD_OFF_OUTLINED, l.warn
        btn = ft.IconButton(ft.Icons.REFRESH, icon_color=l.orn, tooltip="Obnovit",
                            on_click=lambda e: _sync_now(app, app.char))
    else:
        txt, icon, color = "Nepřipojeno.", ft.Icons.CLOUD_OFF_OUTLINED, l.warn
    row: list[ft.Control] = [ft.Icon(icon, size=20, color=color), k.muted(txt, size=13, expand=True)]
    if btn:
        row.append(btn)
    return ft.Row(row, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)
