"""DrD: kouzla kouzelníka (výběr podle pravidel, seslání) a volba oboru na 6. úrovni."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules import drd, drd_kouzla, drd_obory
from ..rules.common import d
from .kit import column


# --- kouzla ------------------------------------------------------------------------------------

def is_wizard(c: dict) -> bool:
    return c.get("system") == "drd" and c.get("cls") == "Kouzelník"


def spell_limit(c: dict) -> int:
    return drd_kouzla.spell_count(c["level"])


def max_mana(c: dict) -> int:
    return max(int(c.get("mana_max", 0)), drd_kouzla.wizard_mana(c["level"], c["attrs"][3]))


def mag_note(c: dict, s: dict) -> str | None:
    """Mág od 6. úrovně sesílá přímo jen vybraná kouzla; ostatní nová kouzla jen přes pomocná kouzla."""
    if c.get("branch") == "Mág" and c["level"] >= 6 and s["source"] == "PPP" and s["name"] not in drd_kouzla.MAG_DIRECT:
        return "mág: jen přes dvířka, dveře nebo bránu"
    return None


def spell_sub(s: dict) -> str:
    parts = [s["mana"], f"dosah {s['reach']}", f"vyvolání {s['cast']}"]
    if s["trap"]:
        parts.append(f"past {s['trap']}")
    return " · ".join(parts)


def spells_section(app, c: dict) -> list[ft.Control]:
    """Sekce Kouzla na kartě postavy."""
    k = app.kit
    known = [drd_kouzla.SPELL_BY_NAME[n] for n in c.get("spells", []) if n in drd_kouzla.SPELL_BY_NAME]
    lim = spell_limit(c)
    rows = [k.row_item(s["name"], s["school"], sub=spell_sub(s), badge=s["source"] if s["source"] == "PPP" else None,
                       on_click=lambda e, s=s: spell_detail(app, c, s, known=True))
            for s in known]
    chance = drd_kouzla.success_chance(c["attrs"][3])
    head = k.section(f"Kouzla {len(known)}/{lim}", ft.TextButton("Vybrat", on_click=lambda e: app.go("kouzla")))
    out = [head, k.list_card(rows) if rows else k.empty("Zatím žádná kouzla. Klepni na Vybrat.")]
    out.append(k.muted(f"Úspěch seslání {chance} % (k% podle inteligence) · magenergie po zaostření vůle "
                       f"{drd_kouzla.wizard_mana(c['level'], c['attrs'][3])} magů.", size=12))
    return out


def kouzla(app):
    """Obrazovka výběru kouzel."""
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    lim = spell_limit(c)
    mana = max_mana(c)
    known = set(c.get("spells", []))
    src = app.ui.get("spell_src", "Vše")
    pool = drd_kouzla.available_spells(c.get("branch"), c["level"])
    if src != "Vše":
        pool = [s for s in pool if s["source"] == src or (src == "Moje" and s["name"] in known)]
    if src == "Moje":
        pool = [s for s in drd_kouzla.SPELLS if s["name"] in known]

    def toggle(s):
        def h(e):
            names = c.setdefault("spells", [])
            if s["name"] in names:
                app.confirm("Zapomenout kouzlo?", "Podle pravidel kouzlo zapomenout nelze. Odebrat ho jen "
                            "z deníku (třeba kvůli překlepu)?",
                            lambda: _remove(app, c, s["name"]), yes_label="Odebrat")
                return
            if len(names) >= lim:
                app.toast(f"Na {c['level']}. úrovni můžeš znát nejvýš {lim} kouzel.")
                return
            names.append(s["name"])
            model.add_history(c, "Nové kouzlo", s["name"])
            app.save(c)
            app.refresh()
        return h

    rows: list[ft.Control] = []
    for s in pool:
        has = s["name"] in known
        too_much = s["min"] is not None and s["min"] > mana and not has
        note = mag_note(c, s)
        sub = spell_sub(s) + (f" · {note}" if note else "") + (" · zatím nemáš dost magenergie" if too_much else "")
        icon = ft.Icons.CHECK_CIRCLE if has else (ft.Icons.BLOCK if too_much else ft.Icons.ADD_CIRCLE_OUTLINE)
        color = l.accent if has else l.muted
        rows.append(ft.Container(ft.Row([
            ft.Column([
                ft.Row([k.text(s["name"], size=15, weight=ft.FontWeight.W_600, color=l.muted if too_much else None),
                        k.badge(s["source"]), k.muted(s["school"], size=12)], spacing=6, wrap=True),
                k.muted(sub, size=12, max_lines=3),
            ], spacing=2, expand=True),
            ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color=l.muted, tooltip="Podrobnosti",
                          on_click=lambda e, s=s: spell_detail(app, c, s, known=s["name"] in known)),
            ft.IconButton(icon, icon_color=color, tooltip="Odebrat" if has else "Naučit se",
                          on_click=None if too_much else toggle(s)),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)))

    info = (f"{c['level']}. úroveň: nejvýš {lim} kouzel · magenergie {mana} magů. Učit se lze jen kouzla, "
            f"na která máš dost magenergie. Kouzla z Pravidel pro pokročilé (PPP) až od 6. úrovně.")
    if c.get("branch") == "Mág" and c["level"] >= 6:
        info += (" Mág sesílá přímo jen: " + ", ".join(drd_kouzla.MAG_DIRECT) +
                 " (a kouzla naučená do 5. úrovně); ostatní přes pomocná kouzla dvířka, dveře a brána.")
    filters = ["Vše", "PPZ", "PPP", "Moje"] if c["level"] >= 6 else ["Vše", "Moje"]
    controls = [
        k.card(k.muted(info, size=13)),
        k.pills(filters, src if src in filters else "Vše", lambda v: app.go("kouzla", spell_src=v)),
        k.list_card(rows) if rows else k.empty("Nic k zobrazení."),
    ]
    if c.get("branch") == "Mág" and c["level"] >= 6:
        controls.append(k.section("Pomocná kouzla mága"))
        controls.append(k.list_card([k.row_item(n, m, sub=t) for n, m, t in drd_kouzla.MAG_HELPERS]))
    return Screen(f"Kouzla {len(known)}/{lim}", [column(controls)])


def _remove(app, c: dict, name: str) -> None:
    if name in c.get("spells", []):
        c["spells"].remove(name)
    app.save(c)
    app.refresh()


def spell_detail(app, c: dict, s: dict, known: bool) -> None:
    k = app.kit
    l = app.look
    rows = [("Magenergie", s["mana"]), ("Past", s["trap"] or "–"), ("Dosah", s["reach"]), ("Rozsah", s["area"]),
            ("Vyvolání", s["cast"]), ("Trvání", s["duration"]),
            ("Obor magie", f"{s['school']} – {drd_kouzla.SCHOOLS.get(s['school'][:2], '')}"),
            ("Pravidla", "Pravidla pro začátečníky" if s["source"] == "PPZ" else "Pravidla pro pokročilé")]
    note = mag_note(c, s)
    body: list[ft.Control] = [k.text(s["desc"], size=14)]
    for a, b in rows:
        body.append(ft.Row([k.muted(a, size=13, expand=True), k.text(b, size=13, weight=ft.FontWeight.W_600)],
                           spacing=8))
    if note:
        body.append(k.muted(note, size=12))
    body.append(k.muted("Podrobný popis účinku je v pravidlech.", size=12, italic=True))

    def cast(e):
        app.close_dialog()

        def do(v):
            spent = max(0, int(v["mana"]))
            if spent > c.get("mana", 0):
                app.toast("Nemáš tolik magenergie.")
                return
            c["mana"] = c.get("mana", 0) - spent
            chance = drd_kouzla.success_chance(c["attrs"][3])
            r = d(100)
            ok = r <= chance
            model.add_history(c, f"Kouzlo {s['name']}", f"k% {r} / {chance} % – {'zdařilo' if ok else 'nezdařilo'}")
            app.save(c)
            app.refresh()
            app.toast(f"{s['name']}: k% = {r} ({chance} %) – {'kouzlo se zdařilo' if ok else 'nezdařilo se'}, "
                      f"−{spent} magů.")
        app.form(f"Seslat: {s['name']}", [("mana", f"Vložená magenergie ({s['mana']})", s["min"] or 1, "int")], do,
                 save_label="Seslat a hodit k%")

    actions: list[ft.Control] = []
    if known:
        actions.append(ft.TextButton("Seslat", on_click=cast))
    actions.append(ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog()))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(s["name"], size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column(body, spacing=6, tight=True, scroll=ft.ScrollMode.AUTO), width=380),
        actions=actions, scrollable=True,
    ))


# --- obory (6. úroveň) ------------------------------------------------------------------------

def branch_cards(app, c: dict, selected: str | None, on_pick) -> list[ft.Control]:
    """Dvě karty oborů povolání s jejich schopnostmi z PPP."""
    k = app.kit
    l = app.look
    out: list[ft.Control] = []
    for name, desc, abil in drd_obory.BRANCHES.get(c["cls"], []):
        sel = name == selected
        rows = [ft.Row([k.text(a, size=13, weight=ft.FontWeight.W_600, expand=True),
                        k.muted(f"od {frm}. úr." if frm > 6 else "", size=12)], spacing=6) for a, frm, _ in abil]
        out.append(k.card(ft.Column([
            ft.Row([k.text(name, size=18, weight=ft.FontWeight.BOLD, head=True, expand=True),
                    ft.Icon(ft.Icons.CHECK_CIRCLE if sel else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            color=l.accent if sel else l.muted)]),
            k.muted(desc, size=13),
            ft.Column(rows, spacing=2),
        ], spacing=6), accent=sel, on_click=lambda e, n=name: on_pick(n)))
    return out


def obor(app):
    """Samostatná obrazovka volby oboru (když postava na 6.+ úrovni obor ještě nemá)."""
    from ..core import Screen

    c = app.char
    k = app.kit
    sel = app.ui.get("branch_pick") or c.get("branch")

    def pick(n):
        app.ui["branch_pick"] = n
        app.refresh()

    def save(e):
        if not sel:
            app.toast("Vyber jeden z oborů.")
            return
        c["branch"] = sel
        model.add_history(c, "Obor", sel)
        app.save(c)
        app.ui["branch_pick"] = None
        app.toast(f"Obor: {sel}")
        app.go("postava")

    controls = [
        k.card(k.muted("Od 6. úrovně se postava rozhodne pro jeden ze dvou oborů svého povolání (Pravidla pro "
                       "pokročilé). Všechny dosavadní schopnosti jí zůstávají, přibudou nové. Volba je trvalá.",
                       size=13)),
        *branch_cards(app, c, sel, pick),
        app.kit.button("Potvrdit obor", save),
    ]
    return Screen("Volba oboru", [column(controls)])


def branch_label(c: dict) -> str:
    return f"{c['cls']} – {c['branch']}" if c.get("branch") else c["cls"]


_ = drd
