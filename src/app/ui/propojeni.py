"""Propojení kampaně podle grafického návrhu: volba (U stolu / Vlastní server PJ), průvodce vlastním serverem
ve 4 krocích, přihlášení PJ klíčem, stůl PJ v místní síti a stav uspaného serveru."""
from __future__ import annotations

import flet as ft

from .. import qr, schema, stul, sync
from ..rules import dh, drd
from . import net
from .kit import column

SYS_NAME = {"dh": dh.NAME, "drd": drd.NAME}


# --- servery PJ v nastavení ----------------------------------------------------------------------

def servers(app) -> list[dict]:
    return app.settings.setdefault("servers", [])


def owned_server(app) -> dict | None:
    """Vlastní server, na kterém je toto zařízení PJ."""
    return next((s for s in servers(app) if s.get("pj_key") and s.get("admin")), None)


def remember_server(app, srv: dict, **kw) -> dict:
    key = sync.server_key(srv)
    for s in servers(app):
        if sync.server_key(s) == key:
            s.update(kw)
            app.save(settings=True)
            return s
    new = {"kind": "own", "url": sync.clean_url(srv["url"]), "key": srv["key"], **kw}
    servers(app).append(new)
    app.save(settings=True)
    return new


def public(srv: dict) -> dict:
    """Údaje serveru, které smí znát hráči (bez klíče PJ)."""
    return {"kind": "own", "url": srv["url"], "key": srv["key"]}


# --- nová kampaň ---------------------------------------------------------------------------------

def new_campaign(app) -> None:
    """Úvod → Nová kampaň (PJ): název a hra, pak volba propojení."""
    def save(v):
        app.ui["new_name"] = (v.get("name") or "").strip() or "Nová kampaň"
        app.ui["new_sys"] = "dh" if v.get("game") == dh.NAME else "drd"
        app.ui["conn"] = "table" if stul.supported() else "own"
        app.go("propojeni")
    app.form("Nová kampaň (PJ)", [("name", "Název kampaně", "", "text"),
                                  ("game", "Hra", drd.NAME, "choice", [drd.NAME, dh.NAME])], save,
             save_label="Pokračovat")


def create_table_campaign(app) -> None:
    system = app.ui.get("new_sys", "drd")
    state = stul.TableState(name=app.ui.get("new_name", "Nová kampaň"), system=system)
    camp = sync.gm_campaign(system, id=state.id, name=state.d["name"], code=state.d["code"],
                            server={"kind": "table"}, table=state.dump())
    app.add_gm(camp)
    app.open_gm(camp["id"])


def create_remote_campaign(app, srv: dict, then_wizard: bool = False) -> None:
    system = app.ui.get("new_sys", "drd")
    name = app.ui.get("new_name", "Nová kampaň")
    cl = app.client(public(srv))

    async def do():
        return await cl.create(name, system)

    def done(row):
        camp = sync.gm_campaign(system, id=row["id"], name=row["name"], code=row["code"],
                                session=row.get("session", 1), server=public(srv), uid=cl.uid)
        app.add_gm(camp)
        app.gm_active = camp["id"]
        if then_wizard:
            app.ui["wiz_step"] = 4
            app.screen = "pruvodce"
        else:
            app.open_gm(camp["id"])
    net.remote(app, "Zakládám kampaň na serveru…", do, after=done)


# --- 1. volba propojení --------------------------------------------------------------------------

def propojeni(app):
    from ..core import Screen

    k = app.kit
    l = app.look
    sel = app.ui.get("conn", "table")
    name = app.ui.get("new_name", "Nová kampaň")
    game = SYS_NAME[app.ui.get("new_sys", "drd")]
    web = not stul.supported()
    own = owned_server(app)

    def pick(v):
        def h(e):
            app.ui["conn"] = v
            app.refresh()
        return h

    def opt(key, icon, title, sub, pros, cons, disabled=False, badge=None):
        on = sel == key and not disabled
        right: ft.Control
        if disabled:
            right = k.badge(badge or "PŘIPRAVUJEME", fg=l.muted)
        elif on:
            right = ft.Icon(ft.Icons.CHECK, size=22, color=l.ok)
        else:
            right = ft.Container(width=22)
        body = ft.Column([
            ft.Row([ft.Icon(icon, size=26, color=l.orn),
                    k.text(title, size=17, weight=ft.FontWeight.BOLD, head=True, expand=True), right],
                   spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            k.muted(sub, size=14),
            k.text("+ " + pros, size=13, color=l.ok),
            k.text("− " + cons, size=13, color=l.warn),
        ], spacing=6)
        return ft.Container(
            body, padding=ft.Padding.all(14), border_radius=ft.BorderRadius.all(l.radius),
            gradient=k.grad(l.card2, l.card), border=ft.Border.all(2 if on else 1, l.orn if on else l.frame),
            shadow=k.glow(16) if on else None, opacity=0.55 if disabled else 1.0,
            on_click=None if disabled else pick(key), ink=not disabled, data="conn:" + key)

    def go_on(e):
        if sel == "table":
            create_table_campaign(app)
        elif own:
            create_remote_campaign(app, own)
        else:
            app.ui.update(wiz_step=1, wiz_create=True, wiz_check=None)
            app.go("pruvodce")

    own_sub = (f"Tvůj server {sync.server_name(own)} je připravený." if own else
               "Tvůj bezplatný Supabase. Průvodce tě provede za 10 minut.")
    controls = [
        k.framed(ft.Column([k.text("Jak se budete propojovat?", size=19, weight=ft.FontWeight.BOLD, head=True),
                            k.muted(f"Kampaň „{name}“ · {game}. Způsob propojení platí pro celou kampaň.", size=14)],
                           spacing=6)),
        opt("table", ft.Icons.WIFI, "U stolu", "Telefony u jednoho stolu na stejné Wi-Fi. Telefon PJ je stůl.",
            "bez internetu a bez účtů, hned", "jen hráči na jednom místě" + (" · ve webové verzi nejde" if web else ""),
            disabled=web, badge="JEN V APLIKACI"),
        opt("own", ft.Icons.DNS_OUTLINED, "Vlastní server PJ", own_sub, "hraje se odkudkoli, data má jen PJ",
            "jednorázové nastavení; po týdnu bez hraní server usne"),
        opt("app", ft.Icons.CLOUD_OUTLINED, "Server aplikace", "Bez nastavování, kampaň jen kódem.",
            "nejjednodušší pro všechny", "placený provoz – zatím nedostupné", disabled=True),
        ft.Container(height=6),
        ft.Row([k.button("Pokračovat", go_on, icon=ft.Icons.CHEVRON_RIGHT, expand=1, height=52)]),
    ]
    return Screen("Nová kampaň", [column(controls)])


# --- 2. průvodce vlastním serverem ---------------------------------------------------------------

def pruvodce(app):
    from ..core import Screen

    step = app.ui.get("wiz_step", 1)
    build = {1: _wiz1, 2: _wiz2, 3: _wiz3, 4: _wiz4}[step]
    return Screen("Vlastní server", [column(build(app))])


def _nav_row(app, next_label="Pokračovat", on_next=None, disabled=False):
    k = app.kit

    def back(e):
        app.back()

    def nxt(e):
        if on_next:
            on_next()
        else:
            app.ui["wiz_step"] = app.ui.get("wiz_step", 1) + 1
            app.refresh()
    return ft.Row([k.button("Zpět", back, primary=False, expand=1),
                   k.button(next_label, nxt, icon=ft.Icons.CHEVRON_RIGHT, expand=1, disabled=disabled)], spacing=8)


def _head(app, title, text):
    k = app.kit
    return k.framed(ft.Column([k.text(title, size=20, weight=ft.FontWeight.BOLD, head=True),
                               k.muted(text, size=14)], spacing=6), padding=16, glow=True)


def _open_url(app, url: str) -> None:
    async def run():
        try:
            await ft.UrlLauncher().launch_url(url)
        except Exception:
            app.toast(url)
    app.run(run())


def _wiz1(app):
    k = app.kit
    return [
        k.steps_bar(1),
        _head(app, "Založ si bezplatný server",
              "Supabase je služba, kde poběží tvoje kampaně. Je zdarma pro malé skupiny."),
        k.framed(k.numbered([
            "Otevři supabase.com a přihlas se (třeba účtem GitHub nebo Google).",
            "Klikni na <b>New project</b>.",
            "Název třeba <b>denik-kampan</b>, region <b>Central EU (Frankfurt)</b>, tarif <b>Free</b>.",
            "Heslo k databázi si ulož do správce hesel – do aplikace ho nezadávej.",
        ]), padding=16),
        k.button("Otevřít supabase.com", lambda e: _open_url(app, "https://supabase.com/dashboard"), primary=False,
                 icon=ft.Icons.OPEN_IN_NEW, height=48),
        ft.Container(height=8),
        _nav_row(app, "Projekt mám"),
    ]


def _wiz2(app):
    k = app.kit
    l = app.look
    lines = schema.SCHEMA.strip().splitlines()

    def copy(e):
        async def run():
            try:
                await ft.Clipboard().set(schema.SCHEMA)
                app.toast("Skript je ve schránce – vlož ho v Supabase do SQL Editoru.")
            except Exception:
                app.toast("Schránka není dostupná.")
        app.run(run())

    code = ft.Container(
        ft.Text("\n".join(lines[:3] + [f"… ({len(lines)} řádků)"]), size=12, color=l.muted),
        padding=ft.Padding.all(12), bgcolor=l.bg, border=ft.Border.all(1, l.border),
        border_radius=ft.BorderRadius.all(l.radius))
    switch = k.framed(ft.Row([
        ft.Column([k.text("Allow anonymous sign-ins", size=15, weight=ft.FontWeight.BOLD),
                   k.muted("Authentication → Sign In / Providers. Hráči se pak nemusí registrovat.", size=13)],
                  spacing=2, expand=True),
        ft.Switch(value=True, active_color=l.hi, disabled=True),
    ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
    return [
        k.steps_bar(2),
        _head(app, "Připrav databázi", "Jeden skript vytvoří tabulky kampaní a pravidla, kdo co smí vidět."),
        code,
        k.button("Zkopírovat skript", copy, primary=False, icon=ft.Icons.CONTENT_COPY, height=48),
        k.framed(k.numbered(["V Supabase vlevo <b>SQL Editor</b> → <b>New query</b>.",
                             "Vlož skript a klikni na <b>Run</b>.",
                             "Má se ukázat <b>Success. No rows returned</b>."]), padding=16),
        k.section("A ještě jedno přepnutí", icon=ft.Icons.SHIELD_OUTLINED),
        switch,
        _nav_row(app, "Hotovo"),
    ]


def _wiz3(app):
    k = app.kit
    l = app.look
    u = app.ui
    url_f = k.field("Project URL", u.get("wiz_url", ""), mono=True)
    key_f = k.field("Publishable key (sb_publishable_…)", u.get("wiz_key", ""), mono=True)
    res = u.get("wiz_check")

    def verify(e):
        url = sync.clean_url(url_f.value or "")
        key = (key_f.value or "").strip()
        u.update(wiz_url=url, wiz_key=key)
        if not url.startswith("https://"):
            app.toast("Vlož Project URL, např. https://abcdefghijkl.supabase.co")
            return
        problem = sync.key_problem(key)
        if problem:
            net.info(app, "Tenhle klíč ne", problem)
            return
        srv = {"kind": "own", "url": url, "key": key}
        cl = app.client(srv)

        async def do():
            r = await cl.check()
            if r["server"] and r["db"] and r["anon"]:
                saved = next((s for s in servers(app) if sync.server_key(s) == sync.server_key(srv)), None)
                pj_key = (saved or {}).get("pj_key") or sync.new_pj_key()
                if not r["owned"] or not r["admin"]:
                    ok = await cl.claim(pj_key)
                    if not ok:
                        r["error"] = ("Server už má svého PJ. Pokud jsi to ty na jiném zařízení, "
                                      "přihlas se klíčem PJ (Úvod → Přihlásit se jako PJ).")
                        return r
                r["admin"] = True
                remember_server(app, srv, pj_key=pj_key, admin=True)
            return r

        def done(r):
            u["wiz_check"] = r
        net.remote(app, "Ověřuji spojení…", do, after=done)

    controls: list[ft.Control] = [
        k.steps_bar(3),
        _head(app, "Spoj aplikaci se serverem", "V Supabase klikni nahoře na Connect a zkopíruj dvě hodnoty."),
        url_f, key_f,
        k.note("Secret key (sb_secret_…) ani heslo k databázi sem nikdy nepatří. Aplikace by je odmítla.",
               ft.Icons.SHIELD_OUTLINED),
        k.button("Ověřit spojení", verify, primary=False, icon=ft.Icons.DNS_OUTLINED, height=48),
    ]
    ok = False
    if res:
        ok = bool(res.get("server") and res.get("db") and res.get("anon") and res.get("admin"))
        rows = [k.check("Server odpovídá", res.get("server"), bad=not res.get("server")),
                k.check("Databáze je připravená", res.get("db"), sub="tabulky Deníku a pravidla přístupu",
                        bad=res.get("server") and not res.get("db")),
                k.check("Anonymní přihlášení je zapnuté", res.get("anon"), bad=res.get("server") and not res.get("anon"))]
        if ok:
            rows.append(k.check("Server je zamčený tvým klíčem PJ", True))
        if res.get("error"):
            rows.append(k.text(res["error"], size=13, color=l.warn))
        controls.append(k.framed(ft.Column(rows, spacing=10)))

    def nxt():
        srv = owned_server(app)
        if u.get("wiz_create") and srv:
            create_remote_campaign(app, srv, then_wizard=True)
        else:
            u["wiz_step"] = 4
            app.refresh()
    controls.append(_nav_row(app, "Pokračovat", nxt, disabled=not ok))
    return controls


def invite_controls(app, camp: dict, size: int = 220) -> list[ft.Control]:
    """QR s pozvánkou + kód kampaně (vlastní server)."""
    k = app.kit
    l = app.look
    srv = camp.get("server") or sync.legacy_server()
    link = sync.invite_link(srv, camp["code"]) if srv and srv.get("kind") == "own" else ""
    img = qr.png(link) if link else None
    out: list[ft.Control] = []
    if img:
        out.append(ft.Container(ft.Image(src=img, width=size, height=size), padding=ft.Padding.all(14),
                                bgcolor="#ffffff", border_radius=ft.BorderRadius.all(8),
                                alignment=ft.Alignment.CENTER, data="qr"))
    out.append(ft.Container(k.text(camp["code"], size=24, weight=ft.FontWeight.BOLD, head=True, color=l.orn),
                            alignment=ft.Alignment.CENTER))

    def share(e):
        async def run():
            try:
                await ft.Share().share_text(f"Pozvánka do kampaně {camp['name']} (Deník dobrodruha): {link}")
            except Exception:
                try:
                    await ft.Clipboard().set(link)
                    app.toast("Odkaz je ve schránce.")
                except Exception:
                    app.toast(link)
        app.run(run())

    def save_img(e):
        async def run():
            try:
                await ft.Share().share_files([ft.ShareFile.from_bytes(img, mime_type="image/png",
                                                                      name="pozvanka.png")])
            except Exception:
                app.toast("Obrázek teď uložit nejde – pošli hráčům odkaz.")
        app.run(run())
    out.append(ft.Row([k.button("Sdílet odkaz", share, primary=False, icon=ft.Icons.SEND_OUTLINED, expand=1, height=44),
                       k.button("Uložit obrázek", save_img, primary=False, icon=ft.Icons.DOWNLOAD_OUTLINED, expand=1,
                                height=44, disabled=img is None)], spacing=8))
    return out


def invite_dialog(app, camp: dict) -> None:
    k = app.kit
    body = [k.muted("QR obsahuje adresu tvého serveru i kód kampaně. Hráč ho naskenuje fotoaparátem, nebo mu pošli "
                    "odkaz – vloží ho v Družině své postavy (Zadat ručně).", size=13)]
    body += invite_controls(app, camp, 200)
    body.append(k.note("Kód sám nestačí – nové hráče schvaluješ v záložce Kampaň.", ft.Icons.SHIELD_OUTLINED))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text("Pozvat hráče", size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
        content=ft.Container(ft.Column(body, spacing=10, tight=True, scroll=ft.ScrollMode.AUTO), width=340),
        actions=[ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]))


def _wiz4(app):
    k = app.kit
    l = app.look
    camp = app.camp
    srv = owned_server(app)
    controls: list[ft.Control] = [
        k.steps_bar(4),
        _head(app, "Server je tvůj. Pozvi hráče",
              "QR obsahuje adresu tvého serveru i kód kampaně. Hráč ho naskenuje a je připojený."),
    ]
    if camp and not sync.is_table(camp):
        controls += invite_controls(app, camp)
    if srv:
        controls.append(k.framed(ft.Column([
            ft.Row([ft.Icon(ft.Icons.KEY_OUTLINED, size=20, color=l.orn),
                    k.text("Tvůj klíč PJ", size=16, weight=ft.FontWeight.BOLD, head=True)], spacing=8),
            k.text(srv["pj_key"], size=20, weight=ft.FontWeight.BOLD, head=True, color=l.orn, align=ft.TextAlign.CENTER),
            k.muted("Ulož si ho. S ním se přihlásíš jako PJ na dalším zařízení; hráčům ho nedávej.", size=13),
        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)))
    controls.append(k.note("Kód sám nestačí – nové hráče schvaluješ v záložce Kampaň.", ft.Icons.SHIELD_OUTLINED))

    def open_table(e):
        if camp:
            app.open_gm(camp["id"])
        else:
            app.go("start")
    controls.append(ft.Row([k.button("Otevřít Stůl PJ" if camp else "Hotovo", open_table, icon=ft.Icons.WORKSPACE_PREMIUM,
                                     expand=1, height=50)]))
    return controls


# --- 3. přihlášení PJ klíčem (další zařízení) ----------------------------------------------------

def pj_login(app):
    from ..core import Screen

    k = app.kit
    l = app.look
    u = app.ui
    url_f = k.field("Adresa serveru (Project URL)", u.get("login_url", ""), mono=True)
    key_f = k.field("Publishable key", u.get("login_key", ""), mono=True)
    pj_f = k.field("Klíč PJ (např. DRAK-7Q2M-K9XP)", "", password=True)
    done = u.get("login_done")

    def login(e):
        url = sync.clean_url(url_f.value or "")
        key = (key_f.value or "").strip()
        pj_key = (pj_f.value or "").strip().upper()
        u.update(login_url=url, login_key=key)
        problem = sync.key_problem(key)
        if not url.startswith("https://") or problem:
            net.info(app, "Zkontroluj údaje", problem or "Vlož adresu serveru, např. https://abcdefghijkl.supabase.co")
            return
        if len(pj_key) < 12:
            app.toast("Klíč PJ má tvar DRAK-XXXX-XXXX.")
            return
        srv = {"kind": "own", "url": url, "key": key}
        cl = app.client(srv)

        async def do():
            if not await cl.claim(pj_key):
                raise sync.SyncError("Klíč PJ nesedí. Najdeš ho v telefonu, kde jsi server nastavil (Stůl PJ → "
                                     "Můj server).")
            remember_server(app, srv, pj_key=pj_key, admin=True)
            rows = await cl.my_campaigns()
            n = 0
            for r in rows:
                if r["id"] in app.gm:
                    continue
                camp = sync.gm_campaign(r["system"], id=r["id"], name=r["name"], code=r["code"],
                                        session=r.get("session", 1), locked=r.get("locked", False), server=srv,
                                        uid=cl.uid)
                camp["notes"] = await cl.notes_get(r["id"]) or []
                app.add_gm(camp)
                n += 1
            return n

        def after(n):
            u["login_done"] = n
        net.remote(app, "Přihlašuji…", do, after=after)

    steps = ft.Column([
        _login_step(app, 1, "Zadáš údaje serveru a klíč PJ", "Najdeš je v telefonu, kde jsi server nastavil.", True),
        _login_step(app, 2, "Telefon se přihlásí jako PJ", "Server ho pozná podle klíče – bez e-mailu a hesla.", True),
        _login_step(app, 3, "Načtou se tvoje kampaně", "I s tajnými poznámkami. Obsah příruček PJ vidí jen PJ.", False),
    ], spacing=14)
    controls: list[ft.Control] = [
        k.framed(ft.Column([k.text("Stát se Pánem jeskyně", size=20, weight=ft.FontWeight.BOLD, head=True),
                            k.muted("Stůl PJ obsahuje tajné poznámky a údaje z příruček Pána jeskyně. Aby je neviděli "
                                    "hráči, otevře se jen ověřenému PJ.", size=14)], spacing=6), padding=16, glow=True),
        url_f, key_f, pj_f,
        ft.Row([k.button("Přihlásit klíčem PJ", login, icon=ft.Icons.KEY_OUTLINED, expand=1, height=50)]),
        k.section("Jak to funguje"), k.framed(steps),
    ]
    if done is not None:
        controls.append(k.framed(ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=22, color=l.ok),
            ft.Column([k.text("Přihlášen jako PJ", size=16, weight=ft.FontWeight.BOLD, head=True, color=l.ok),
                       k.muted(f"Načteno kampaní: {done}. Najdeš je na úvodu v části Vedu hru.", size=13)],
                      spacing=2, expand=True)], spacing=10)))
    controls.append(k.note("Hráči se dál přihlašují neviditelně (bez e-mailu). PJ se přihlásí jednou, pak už jen "
                           "otevře Stůl PJ."))
    return Screen("Pán jeskyně", [column(controls)])


def _login_step(app, n, title, sub, filled):
    k = app.kit
    l = app.look
    return ft.Row([
        ft.Container(k.text(str(n), size=14, weight=ft.FontWeight.BOLD, head=True,
                            color=l.on_accent if filled else l.ink), width=28, height=28,
                     alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(14),
                     bgcolor=l.orn if filled else l.card2, border=ft.Border.all(1, l.orn)),
        ft.Column([k.text(title, size=15, weight=ft.FontWeight.BOLD), k.muted(sub, size=13)], spacing=2, expand=True),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)


# --- bloky pro Stůl PJ: stůl v místní síti, uspaný server -----------------------------------------

def stul_block(app, camp: dict) -> list[ft.Control]:
    """Kampaň u stolu: stav stolu, kód, zařízení u stolu (podle návrhu „U stolu – PJ otevírá stůl“)."""
    k = app.kit
    l = app.look
    host = app.hosts.get(camp["id"])
    running = bool(host and host.running)
    ip = stul.local_ip() if running else None
    state = app.table_state(camp)

    def reopen(e):
        async def run():
            ok = await app.open_table(camp)
            app.refresh()
            if not ok:
                net.info(app, "Stůl se neotevřel", (host.error if host else None) or stul.WEB_MSG)
        app.run(run())

    head = k.framed(ft.Row([
        ft.Icon(ft.Icons.WIFI if running else ft.Icons.WIFI_OFF, size=24, color=l.ok if running else l.warn),
        ft.Column([k.text("Stůl je otevřený" if running else "Stůl je zavřený", size=18, weight=ft.FontWeight.BOLD,
                          head=True),
                   k.muted((f"Wi-Fi · adresa {ip} · bez internetu to stačí" if ip else
                            "Wi-Fi nebo hotspot telefonu · bez internetu to stačí") if running else
                           ((host.error if host and host.error else None) or "Otevři stůl, ať se hráči můžou připojit."),
                           size=13)], spacing=2, expand=True),
        k.pj_badge(),
    ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER), glow=running)
    out: list[ft.Control] = [head]
    if not running:
        out.append(k.button("Otevřít stůl", reopen, icon=ft.Icons.WIFI, height=48, disabled=not stul.supported()))
    out.append(k.muted("Hráči na stejné Wi-Fi klepnou v Družině své postavy na Hledat stůl, nebo zadají kód stolu.",
                       size=14))
    out.append(ft.Container(k.text(f"STŮL {state.d['code']}", size=22, weight=ft.FontWeight.BOLD, head=True,
                                   color=l.orn), alignment=ft.Alignment.CENTER))
    devices = [m for m in camp.get("members") or [] if m.get("role") != "gm"]
    approved = [m for m in devices if m.get("status") == "approved"]
    out.append(k.section(f"U stolu {len(approved)}/{len(devices)}" if devices else "U stolu",
                         icon=ft.Icons.GROUPS_OUTLINED))
    rows: list[ft.Control] = []
    for m in devices:
        s = m.get("snapshot") or {}
        pend = m.get("status") != "approved"
        online = sync.is_online(m)
        sub = "čeká na schválení" if pend else ("připojen" if online else "offline · dorovná se")
        trailing = (k.button("Přijmout", lambda e, m=m: set_status(app, camp, m, "approved"), height=38,
                             icon=ft.Icons.CHECK) if pend else k.badge("OK" if online else "OFF"))
        rows.append(k.row_item(s.get("name", "?"), sub=sub, trailing=trailing))
    out.append(k.list_card(rows) if rows else k.empty("Zatím u stolu nikdo není."))
    out.append(k.note("Data jsou jen v telefonech u stolu. Když telefon PJ zavře stůl, kampaň zůstane v něm a příště "
                      "se otevře znovu.", ft.Icons.INFO_OUTLINE))
    return out


def set_status(app, camp: dict, m: dict, status: str) -> None:
    cl = app.client(camp.get("server"), camp)
    name = (m.get("snapshot") or {}).get("name", "Hráč")

    async def do():
        if status == "approved":
            await cl.set_status(camp["id"], m["user_id"], "approved")
        else:
            await cl.kick(camp["id"], m["user_id"])
        await app.sync_gm_now(camp)
    net.remote(app, "Ukládám…", do, f"{name} je v družině." if status == "approved" else f"{name} odmítnut.")


def spi_block(app, camp: dict) -> list[ft.Control]:
    """Vlastní server neodpovídá – nejspíš spí (podle návrhu „Stav serveru – uspaný“)."""
    k = app.kit
    l = app.look
    srv = camp.get("server") or {}
    ref = sync.server_name(srv).split(".")[0]

    def retry(e):
        async def run():
            await app.sync_gm_now(camp)
            app.refresh()
            app.toast("Server běží." if camp.get("online") else "Server zatím neodpovídá.")
        app.run(run())

    return [
        k.framed(ft.Row([ft.Icon(ft.Icons.NIGHTLIGHT_OUTLINED, size=30, color=l.warn),
                         ft.Column([k.text("Server spí", size=19, weight=ft.FontWeight.BOLD, head=True, color=l.warn),
                                    k.muted("Bezplatný Supabase se po týdnu bez hraní uspí. Hráči se teď nepřipojí. "
                                            "(Nebo nejsi připojený k internetu.)", size=13)], spacing=2, expand=True)],
                        spacing=12), padding=16, border_color=l.warn),
        k.framed(k.numbered(["Otevři svůj projekt na supabase.com.", "Klikni na <b>Restore project</b>.",
                             "Za pár minut se tu stav změní na Běží."]), padding=16),
        k.button("Otevřít můj projekt", lambda e: _open_url(app, f"https://supabase.com/dashboard/project/{ref}"),
                 primary=False, icon=ft.Icons.OPEN_IN_NEW, height=48),
        k.button("Zkusit znovu", retry, primary=False, icon=ft.Icons.CHECK, height=48),
        k.section("Mezitím", icon=ft.Icons.INFO_OUTLINE),
        k.muted("Hraj dál – úpravy hráčů a zprávy se uloží v telefonu a odešlou se, až server poběží. "
                "Nebo založ kampaň u stolu a hrajte bez internetu.", size=14),
    ]


def my_server_rows(app, camp: dict) -> list[ft.Control]:
    k = app.kit
    srv = camp.get("server") or {}
    saved = next((s for s in servers(app) if srv.get("url") and sync.server_key(s) == sync.server_key(srv)), None)
    rows = [k.row_item("Typ", sub="U stolu · data v telefonu PJ" if sync.is_table(camp) else "Vlastní server PJ · Supabase Free"),
            k.row_item("Adresa", sub=sync.server_name(srv) if not sync.is_table(camp) else (stul.local_ip() or "Wi-Fi"))]
    n = sum(1 for g in app.gm.values() if (g.get("server") or {}).get("url") == srv.get("url")) if srv.get("url") else 1
    rows.append(k.row_item("Kampaně", sub=camp["name"] if n == 1 else f"{n} kampaně na serveru", right=str(n)))
    if saved and saved.get("pj_key"):
        def show_key(e):
            net.info(app, "Klíč PJ", "S tímto klíčem se přihlásíš jako PJ na dalším zařízení (Úvod → Přihlásit se "
                                     "jako PJ). Hráčům ho nedávej.", big=saved["pj_key"])
        rows.append(k.row_item("Klíč PJ", sub="••••-••••-••••", on_click=show_key,
                               trailing=ft.Icon(ft.Icons.VISIBILITY_OUTLINED, color=app.look.orn)))
    return [k.section("Můj server", icon=ft.Icons.DNS_OUTLINED), k.list_card(rows)]
