"""Obrazovka Družina – připojení ke hře, členové, hody družiny, obrázky od PJ, sdílení.

Každá hra má svou Družinu ve svém vzhledu (DrD Fire, DH Ice); kampaň patří vždy k jedné hře.
"""
from __future__ import annotations

import time

import flet as ft

from .. import sync
from ..rules import dh, drd
from .kit import column

SYS_NAME = {"dh": dh.NAME, "drd": drd.NAME}


def _ago(ts: float) -> str:
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
        sub = (f"{'PJ' if camp['role'] == 'gm' else 'Hráč'} · sezení {camp['session']} · kód {camp['code']}")
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
    controls = _campaign_view(app, c, camp) if camp else _join_view(app, c)
    return Screen("Družina", [column(controls)])


# --- nepřipojená postava -------------------------------------------------------------------------

def _join_view(app, c: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    game = SYS_NAME[c["system"]]

    def join(e):
        def do(v):
            code = sync.normalize_code(v.get("code", ""))
            if code is None:
                app.toast("Kód má 6 znaků, např. K7P-42Q.")
                return
            try:
                sync.join_campaign(c, code)
            except sync.NotConfigured:
                _info(app, "Připojení zatím není zapnuté",
                      f"Kód {code} je v pořádku, ale aplikace ještě nemá server pro družinu (Supabase). "
                      "Až ho tvůrce aplikace nastaví, připojíš se tímto kódem a tvoje postava se objeví "
                      "u ostatních. Zatím můžeš kampaň založit jako PJ – jen v tomto zařízení.")
                return
            app.save(c)
            app.refresh()
        app.form("Připojit se ke kampani", [("code", "Kód od PJ (např. K7P-42Q)", "", "text")], do,
                 save_label="Připojit")

    def create(e):
        def do(v):
            sync.create_campaign(c, v.get("name", ""))
            app.save(c)
            app.refresh()
            app.toast(f"Kampaň založena, kód {c['campaign']['code']}.")
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
            k.row_item("Ostatní hráči", trailing=None, sub="jméno, povolání, úroveň, životy a hody"),
            k.row_item("PJ", sub="celý deník postavy – vlastnosti, batoh; může házet skrytě a sdílet mapy"),
            k.row_item("Jen ty (a PJ)", sub="batoh a osobní poznámky v Deníku"),
        ]),
        _offline_note(app),
    ]


# --- postava v kampani -----------------------------------------------------------------------------

def _campaign_view(app, c: dict, camp: dict) -> list[ft.Control]:
    k = app.kit
    l = app.look
    gm = camp["role"] == "gm"

    def show_code(e):
        _info(app, "Kód pro připojení",
              f"Pošli hráčům kód {camp['code']}. Zadají ho v Družině své postavy pro {SYS_NAME[camp['system']]}.",
              big=camp["code"])

    def next_session(e):
        camp["session"] += 1
        app.save(c)
        app.refresh()

    def toggle(key):
        def h(e):
            camp[key] = bool(e.control.value)
            app.save(c)
            app.refresh()
        return h

    def leave(e):
        def yes(ev):
            app.close_dialog()
            sync.leave(c)
            app.save(c)
            app.refresh()
            app.toast("Kampaň opuštěna. Postava zůstala v telefonu.")
        app.page.show_dialog(ft.AlertDialog(
            title=k.text("Opustit kampaň?", size=19, weight=ft.FontWeight.BOLD, head=True),
            content=k.muted("Postava ti zůstane i s celým deníkem. Do kampaně se můžeš vrátit znovu kódem.", size=14),
            actions=[ft.TextButton("Zrušit", on_click=lambda ev: app.close_dialog()),
                     ft.TextButton("Opustit", on_click=yes)]))

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

    # členové: zatím jen ty (ostatní přibudou se serverem)
    snap = sync.snapshot(c)
    me_sub = f"{c.get('race', '')} · {c.get('cls', '')} · {c.get('level', 1)}. úroveň"
    me = ft.Column([
        ft.Row([k.text(f"{c['name']} (ty)", size=16, weight=ft.FontWeight.BOLD, expand=True),
                k.badge("PJ" if gm else "ONLINE" if camp.get("online") else "OFFLINE")]),
        k.muted(me_sub, size=13),
        k.bar(snap["hp"] or 0, snap["hp_max"] or 1, l.hp, l.hp_dark, height=12) if snap["hp"] is not None
        else k.muted("životy nesdílíš", size=12),
    ], spacing=4)
    members = k.list_card([
        ft.Container(me, padding=ft.Padding.symmetric(vertical=2)),
        k.row_item("Ostatní členové", sub="objeví se po připojení k serveru – každý se svým pruhem životů "
                                          "a stavem online / offline"),
    ])

    rolls = sync.rolls(c)[:8] if camp["share_rolls"] else []
    roll_rows = [k.row_item(f"{c['name']} · {h['label']}", h["value"], sub=_ago(h["ts"])) for h in rolls]
    rolls_block = (k.list_card(roll_rows) if roll_rows else
                   k.empty("Zatím žádné hody od připojení." if camp["share_rolls"] else "Sdílení hodů máš vypnuté."))

    pend = sync.pending(c)
    controls: list[ft.Control] = [
        head,
        _offline_note(app, pend),
        k.section(f"Družina", icon=ft.Icons.GROUPS_OUTLINED),
        members,
        k.section("Hody družiny", icon=ft.Icons.CASINO_OUTLINED,
                  trailing=ft.TextButton("Kostky", on_click=lambda e: app.go("kostky"))),
        rolls_block,
        k.muted("Skryté hody PJ uvidí ostatní jen jako „skrytý hod – jen pro PJ“.", size=12),
        k.section("Sdílené obrázky", icon=ft.Icons.MAP_OUTLINED),
        k.empty("Mapy a obrázky od PJ se tu objeví a uloží se ti do Deníku." if not gm else
                "Mapy a obrázky sdílíš z Deníku (Obrázky) – po připojení k serveru je uvidí celá družina."),
        k.section("Sdílení", icon=ft.Icons.TUNE),
        k.card(ft.Column([
            ft.Switch(label="Sdílet moje hody s družinou", value=camp["share_rolls"],
                      active_color=l.hi, on_change=toggle("share_rolls")),
            ft.Switch(label="Sdílet moje životy s družinou", value=camp["share_hp"],
                      active_color=l.hi, on_change=toggle("share_hp")),
            k.muted("Batoh a poznámky vidí jen PJ. Osobní poznámky v Deníku se nesdílí.", size=12),
        ], spacing=4)),
    ]
    if gm:
        controls += [k.section("Pro PJ", icon=ft.Icons.SHIELD_OUTLINED),
                     k.card(k.stepper(camp["session"], lambda e: _session(app, c, -1), next_session,
                                      label="Sezení", sub="+1 na začátku každého hraní"))]
    controls.append(ft.Row([k.button("Opustit kampaň", leave, primary=False, icon=ft.Icons.LOGOUT, expand=1)]))
    return controls


def _session(app, c: dict, d: int) -> None:
    camp = c["campaign"]
    camp["session"] = max(1, camp["session"] + d)
    app.save(c)
    app.refresh()


def _offline_note(app, pending: int = 0) -> ft.Control:
    k = app.kit
    l = app.look
    if sync.configured():
        txt = "Propojeno se serverem družiny." + (f" Odesílám {pending} změn…" if pending else "")
        icon, color = ft.Icons.CLOUD_DONE_OUTLINED, l.ok
    else:
        txt = ("Offline – server pro družinu ještě není nastavený. Vše funguje v tomto telefonu; "
               + (f"{pending} hodů čeká na odeslání a " if pending else "")
               + "hody a životy se odešlou po připojení.")
        icon, color = ft.Icons.CLOUD_OFF_OUTLINED, l.warn
    return ft.Row([ft.Icon(icon, size=20, color=color), k.muted(txt, size=13, expand=True)], spacing=10,
                  vertical_alignment=ft.CrossAxisAlignment.START)


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
