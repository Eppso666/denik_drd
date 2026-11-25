"""DrD: kouzla kouzelníka a hraničáře, mimosmyslové schopnosti, alchymie, aktivní kouzla a volba oboru."""
from __future__ import annotations

import re

import flet as ft

from .. import model
from ..rules import drd, drd_alchymie, drd_hranicar, drd_kouzla, drd_obory, drd_ucinky
from ..rules.common import d
from . import spell_result
from .kit import column, matches


# --- kouzla ------------------------------------------------------------------------------------

def is_wizard(c: dict) -> bool:
    return c.get("system") == "drd" and c.get("cls") == "Kouzelník"


def is_ranger(c: dict) -> bool:
    return c.get("system") == "drd" and c.get("cls") == "Hraničář"


def is_alchemist(c: dict) -> bool:
    return c.get("system") == "drd" and c.get("cls") == "Alchymista"


def find_spell(name: str) -> dict | None:
    return drd_kouzla.SPELL_BY_NAME.get(name) or drd_hranicar.SPELL_BY_NAME.get(name)


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
    if is_ranger(c):
        return ranger_section(app, c)
    if is_alchemist(c):
        return alchemy_section(app, c)
    if not is_wizard(c):
        return []
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
    if is_ranger(c):
        return ranger_kouzla(app)
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
    q = app.ui.get("spell_q", "")
    if q:
        pool = [s for s in pool if matches(q, s["name"], s["desc"], s["school"], drd_kouzla.SCHOOLS.get(s["school"][:2]))]

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
        color = l.hi if has else l.muted
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
        k.search(q, lambda v: app.go("kouzla", spell_q=v), "Hledat kouzlo (název, obor, účinek)…"),
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
    ranger = "from_level" in s
    rows = [("Magenergie", s["mana"]), ("Past", s["trap"] or "–"), ("Dosah", s["reach"]), ("Rozsah", s["area"]),
            ("Vyvolání", s["cast"]), ("Trvání", s["duration"])]
    if ranger:
        if s.get("freq"):
            rows.append(("Četnost", s["freq"]))
        rows.append(("Skupina", f"{s['school']} · od {s['from_level']}. úrovně"))
    else:
        rows.append(("Obor magie", f"{s['school']} – {drd_kouzla.SCHOOLS.get(s['school'][:2], '')}"))
    rows.append(("Pravidla", "Pravidla pro začátečníky" if s["source"] == "PPZ" else "Pravidla pro pokročilé"))
    note = None if ranger else mag_note(c, s)
    body: list[ft.Control] = [k.text(s["desc"], size=14)]
    for a, b in rows:
        body.append(ft.Row([k.muted(a, size=13, expand=True), k.text(b, size=13, weight=ft.FontWeight.W_600)],
                           spacing=8))
    if note:
        body.append(k.muted(note, size=12))
    if s["name"] == "Zmam osobu":
        body.append(k.muted("Tabulka zmámení (Int terče: úspěch · kontrola · magů na úroveň): " + "; ".join(
            f"{'≤' if top < 99 else '21+'}{top if top < 99 else ''}: {p} % · {ch} · {per or '–'}"
            for top, p, ch, per in drd_hranicar.CHARM), size=12))
    body.append(k.muted("Podrobný popis účinku je v pravidlech.", size=12, italic=True))

    def cast(e):
        app.close_dialog()

        def do(v):
            spent = max(0, int(v["mana"]))
            if spent > c.get("mana", 0):
                app.toast("Nemáš tolik magenergie.")
                return
            c["mana"] = c.get("mana", 0) - spent
            roll = chance = None
            word = None
            if ranger:
                ok, txt, word = True, "sesláno", "Sesláno"
            else:
                chance = drd_kouzla.success_chance(c["attrs"][3])
                roll = d(100)
                ok, special = drd.pct_outcome(roll, chance, c["level"])
                word = special.capitalize() if special else None
                txt = drd.pct_text(roll, chance, c["level"])[1]
            model.add_history(c, f"Kouzlo {s['name']}", txt)
            n = int(v.get("dur") or 0)
            if ok and n > 0:
                add_active(c, s["name"], n, v.get("unit") or "kolo")
            app.save(c)
            spell_result.show(app, c, s["name"], spent, ok, roll, chance, word=word, trap=s.get("trap") or None,
                              duration=s.get("duration") if s.get("trap") else None)
        dn, du = parse_duration(s["duration"])
        fields = [("mana", f"Vložená magenergie ({s['mana']})", s["min"] or 1, "int")]
        if drd_ucinky.effect(s["name"]):
            def calc(val, name=s["name"]):
                try:
                    m = int(str(val or 0).split(".")[0] or 0)
                except ValueError:
                    m = 0
                return (drd_ucinky.summary(name, m) or "") + f" · máš {int(c.get('mana', 0))} magů"
            fields.append(("calc", "", ("mana", calc), "calc"))
        fields += [("dur", "Sledovat trvání – počet (0 = ne)", dn, "int"),
                   ("unit", "Jednotka", du, "choice", UNITS)]
        app.form(f"Seslat: {s['name']}", fields, do, save_label="Seslat" if ranger else "Seslat a hodit k%")

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
                            color=l.hi if sel else l.muted)]),
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
        table = drd.class_mana(c["cls"], c["level"], c["attrs"], sel)
        if table and table > int(c.get("mana_max", 0)):
            c["mana"] = min(table, int(c.get("mana", 0)) + table - int(c.get("mana_max", 0)))
            c["mana_max"] = table
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


# --- aktivní kouzla a účinky s trváním ---------------------------------------------------------

UNITS = ["kolo", "směna", "hodina", "den"]
_UNIT_RE = [(r"kol", "kolo"), (r"směn", "směna"), (r"hod", "hodina"), (r"d(en|ny|ní)", "den")]


def parse_duration(text: str) -> tuple[int, str]:
    """„3 směny“ → (3, směna); „podle magenergie“, „ihned“, „stále“ → (0, kolo)."""
    m = re.match(r"\s*(\d+)\s*(\S+)", text or "")
    if not m:
        return 0, "kolo"
    for pat, unit in _UNIT_RE:
        if re.match(pat, m.group(2)):
            return int(m.group(1)), unit
    return 0, "kolo"


def add_active(c: dict, name: str, n: int, unit: str) -> None:
    c.setdefault("active", []).append({"id": model.new_id(), "name": name, "left": int(n), "unit": unit})


def tick(c: dict, unit: str) -> list[str]:
    """Uplyne jedna jednotka času: sníží zbývající trvání účinků v této jednotce, vrátí skončené."""
    done = []
    for a in list(c.get("active", [])):
        if a["unit"] == unit:
            a["left"] -= 1
            if a["left"] <= 0:
                c["active"].remove(a)
                done.append(a["name"])
    return done


def _unit_word(unit: str, n: int) -> str:
    forms = {"kolo": ("kolo", "kola", "kol"), "směna": ("směna", "směny", "směn"),
             "hodina": ("hodina", "hodiny", "hodin"), "den": ("den", "dny", "dní")}[unit]
    return forms[0] if n == 1 else forms[1] if 2 <= n <= 4 else forms[2]


def active_section(app, c: dict) -> list[ft.Control]:
    """Sekce Aktivní kouzla a účinky na kartě postavy (odpočet trvání)."""
    k = app.kit
    act = c.get("active", [])

    def add(e):
        def save(v):
            if not v.get("name"):
                return
            add_active(c, v["name"], max(1, int(v.get("n") or 1)), v.get("unit") or "kolo")
            app.save(c)
            app.refresh()
        app.form("Nový účinek", [("name", "Název (kouzlo, lektvar…)", "", "text"),
                                ("n", "Trvání", 1, "int"), ("unit", "Jednotka", "kolo", "choice", UNITS)], save,
                 save_label="Přidat")

    def remove(a):
        def h(e):
            if a in c.get("active", []):
                c["active"].remove(a)
            app.save(c)
            app.refresh()
        return h

    def step(unit):
        def h(e):
            done = tick(c, unit)
            app.save(c)
            app.refresh()
            app.toast("Skončilo: " + ", ".join(done) if done else f"Uplynula 1 {unit}.")
        return h

    head = k.section("Aktivní účinky", ft.TextButton("Přidat", on_click=add))
    if not act:
        return [head, k.empty("Žádné. Při seslání kouzla můžeš nechat odpočítávat jeho trvání.")]
    rows = [k.row_item(a["name"], f"{a['left']} {_unit_word(a['unit'], a['left'])}",
                       trailing=ft.IconButton(ft.Icons.CLOSE, tooltip="Ukončit", icon_color=app.look.muted,
                                              on_click=remove(a)))
            for a in act]
    units = [u for u in UNITS if any(a["unit"] == u for a in act)]
    btns = [app.kit.button(f"+1 {u}", step(u), primary=False, expand=1, height=40) for u in units]
    return [head, k.list_card(rows), ft.Row(btns, spacing=8)]


# --- hraničář: kouzla a mimosmyslové schopnosti ---------------------------------------------------

def ranger_section(app, c: dict) -> list[ft.Control]:
    k = app.kit
    spells = drd_hranicar.ranger_spells(c["level"], c.get("branch"))
    out: list[ft.Control] = []
    if spells:
        groups = list(dict.fromkeys(s["school"] for s in spells))
        out += [k.section(f"Kouzla {len(spells)}", ft.TextButton("Seznam", on_click=lambda e: app.go("kouzla"))),
                k.card(k.muted("Hraničář zná všechna kouzla svého povolání" +
                               (f" a oboru ({', '.join(groups[1:])})" if len(groups) > 1 else "") +
                               ". Kouzla se nehází na úspěch – stačí magenergie.", size=13),
                       on_click=lambda e: app.go("kouzla"))]
    out += abilities_section(app, c)
    return out


def ranger_kouzla(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    spells = drd_hranicar.ranger_spells(c["level"], c.get("branch"))
    groups = ["Vše"] + list(dict.fromkeys(s["school"] for s in spells))
    grp = app.ui.get("rspell_grp", "Vše")
    if grp not in groups:
        grp = "Vše"
    q = app.ui.get("spell_q", "")
    shown = [s for s in spells if (grp == "Vše" or s["school"] == grp) and
             matches(q, s["name"], s["desc"], s["school"])]
    rows = []
    for s in shown:
        locked = s["from_level"] > c["level"]
        low = s["min"] is not None and s["min"] > int(c.get("mana", 0))
        sub = " · ".join(x for x in (s["mana"], f"dosah {s['reach']}", f"vyvolání {s['cast']}", s.get("freq"),
                                      f"od {s['from_level']}. úrovně" if locked else "",
                                      "teď málo magenergie" if low and not locked else "") if x)
        rows.append(k.row_item(s["name"], s["school"], sub=sub,
                               badge=s["source"] if s["source"] == "PPP" else None,
                               on_click=lambda e, s=s, lk=locked: spell_detail(app, c, s, known=not lk)))
    info = (f"Magenergie {c.get('mana', 0)}/{c.get('mana_max', 0)} magů. Hraničář kouzlí od 2. úrovně, "
            "kouzla druida a chodce (PPP) od 6. úrovně podle oboru.")
    controls = [k.card(k.muted(info, size=13)),
                k.search(q, lambda v: app.go("kouzla", spell_q=v), "Hledat kouzlo…"),
                k.pills(groups, grp, lambda v: app.go("kouzla", rspell_grp=v)),
                k.list_card(rows) if rows else k.empty("Nic k zobrazení.")]
    if c.get("branch") == "Druid" and c["level"] >= 6:
        controls.append(k.section("Pomocná lesní kouzla"))
        controls.append(k.list_card([
            k.row_item(n, f"{m} magů", sub=f"od {lv}. úrovně · vyvolání 2 směny · obnoví lesní kouzla")
            for n, m, lv in drd_hranicar.DRUID_HELPERS]))
    _ = l
    return Screen(f"Kouzla {len(spells)}", [column(controls)])


def abilities_section(app, c: dict) -> list[ft.Control]:
    k = app.kit
    slots = drd_hranicar.ability_slots(c["level"], c.get("branch"))
    have = c.setdefault("abilities_mind", [])
    if not slots and not have:
        return []  # schopnosti se ukazují až od úrovně, na které je postava má

    def add(e):
        free = [a for a in drd_hranicar.ABILITIES if a not in [h["name"] for h in have]]

        def roll(ev):
            app.close_dialog()
            r = d(100)
            name = drd_hranicar.ability_roll(r)
            if name in [h["name"] for h in have]:
                app.toast(f"Padlo {r}: {name} – tu už máš, vyber si jinou.")
                return
            _learn(name, f"k% {r}")

        def pick(name):
            def h(ev):
                app.close_dialog()
                _learn(name, "volba")
            return h

        body: list[ft.Control] = [k.muted("První schopnost určuje k% (1–40 telekineze, 41–75 pyrokineze, "
                                          "76–100 telepatie), další si druid a chodec volí.", size=13)]
        if not have:
            body.append(k.button("Hodit k%", roll))
        body += [k.button(n, pick(n), primary=False) for n in free]
        app.page.show_dialog(ft.AlertDialog(
            title=k.text("Mimosmyslová schopnost", size=19, weight=ft.FontWeight.BOLD, head=True),
            bgcolor=app.look.card, content=ft.Container(ft.Column(body, spacing=8, tight=True), width=340),
            actions=[ft.TextButton("Zrušit", on_click=lambda ev: app.close_dialog())]))

    def _learn(name, how):
        have.append({"name": name, "since": c["level"]})
        model.add_history(c, "Mimosmyslová schopnost", f"{name} ({how})")
        app.save(c)
        app.refresh()

    def detail(h):
        def show(e):
            g = drd_hranicar.ability_grade(c["level"], h["since"])
            body: list[ft.Control] = [k.text(drd_hranicar.ABILITY_DESC[h["name"]], size=14),
                                      k.text(f"Stupeň znalosti {g}: {drd_hranicar.ability_value(h['name'], g)}",
                                             size=14, weight=ft.FontWeight.W_600)]
            if h["name"] == "Telepatie":
                for act, dang, mod, who, attr in drd_hranicar.MIND_READING:
                    body.append(k.muted(f"{act}: nebezpečnost {dang} {mod} · hází {who} · {attr}", size=12))
            body.append(k.muted("Před použitím 1 směna soustředění, nejvýš jednou za 7 hodin. "
                                "Únava jako u nevyčerpávajících kouzel.", size=12))

            def forget(ev):
                have.remove(h)
                app.save(c)
                app.close_dialog()
                app.refresh()
            app.page.show_dialog(ft.AlertDialog(
                title=k.text(h["name"], size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
                content=ft.Container(ft.Column(body, spacing=6, tight=True), width=380),
                actions=[ft.TextButton("Odebrat", on_click=forget),
                         ft.TextButton("Zavřít", on_click=lambda ev: app.close_dialog())]))
        return show

    rows = [k.row_item(h["name"], f"stupeň {drd_hranicar.ability_grade(c['level'], h['since'])}",
                       sub=drd_hranicar.ability_value(h["name"], drd_hranicar.ability_grade(c["level"], h["since"])),
                       on_click=detail(h)) for h in have]
    trail = ft.TextButton("Přidat", on_click=add) if len(have) < max(slots, 1) and len(have) < 3 else None
    out = [k.section(f"Mimosmyslové schopnosti {len(have)}/{slots}", trail)]
    out.append(k.list_card(rows) if rows else k.empty("Klepni na Přidat a hoď k%."))
    return out


# --- alchymista: výroba předmětů ------------------------------------------------------------------

def alchemy_section(app, c: dict) -> list[ft.Control]:
    k = app.kit
    chance = drd_alchymie.success_chance(c["attrs"][1])
    return [k.section("Alchymie", ft.TextButton("Výroba", on_click=lambda e: app.go("alchymie"))),
            k.card(k.muted(f"Truhla: {c.get('mana', 0)} magů · {c.get('raw', 0)} zl surovin. Úspěch výroby "
                           f"{chance} % (k% podle obratnosti). Neúspěch spotřebuje magy i suroviny.", size=13),
                   on_click=lambda e: app.go("alchymie"))]


def alchymie(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    groups = drd_alchymie.GROUPS
    grp = app.ui.get("alch_grp") or groups[0]
    q = app.ui.get("alch_q", "")
    if q:
        shown = [i for i in drd_alchymie.ITEMS if matches(q, i["name"], i["desc"], i["base"], i["group"])]
    else:
        shown = [i for i in drd_alchymie.ITEMS if i["group"] == grp]
    rows = []
    for it in shown:
        prob = drd_alchymie.craft_problem(c, it)
        sub = " · ".join(x for x in (f"suroviny {it['raw']} zl", f"základ {it['base']}", f"výroba {it['make']}",
                                      prob or "") if x)
        rows.append(k.row_item(it["name"], it["mana"] if it["mags"] else "bez magů", sub=sub,
                               badge=f"sféra {it['sphere']}" if it["sphere"] else None,
                               on_click=lambda e, it=it: craft_dialog(app, c, it)))

    def adj_raw(e):
        def save(v):
            c["raw"] = max(0, int(v["raw"]))
            app.save(c)
            app.refresh()
        app.form("Suroviny v truhle", [("raw", "Zlaťáků surovin", c.get("raw", 0), "int")], save)

    controls = [
        k.card(ft.Row([k.muted(f"Truhla: {c.get('mana', 0)}/{c.get('mana_max', 0)} magů · "
                               f"{c.get('raw', 0)} zl surovin", size=14, expand=True),
                       ft.TextButton("Suroviny", on_click=adj_raw)])),
        k.search(q, lambda v: app.go("alchymie", alch_q=v), "Hledat předmět…"),
    ]
    if not q:
        controls.append(k.pills(groups, grp, lambda v: app.go("alchymie", alch_grp=v)))
    controls.append(k.list_card(rows) if rows else k.empty("Nic k zobrazení."))
    controls.append(k.muted("Předměty z Pravidel pro začátečníky. Výroba kratší než 6 směn vyžaduje klid "
                            "a soustředění; „doma“ = jen v laboratoři.", size=12))
    return Screen("Alchymie", [column(controls)])


def craft_dialog(app, c: dict, it: dict) -> None:
    k = app.kit
    l = app.look
    rows = [("Magenergie", it["mana"]), ("Suroviny", f"{it['raw']} zl"), ("Základ", it["base"]),
            ("Trvání", it["duration"]), ("Výroba", it["make"])]
    body: list[ft.Control] = [k.text(it["desc"], size=14)]
    for a, b in rows:
        body.append(ft.Row([k.muted(a, size=13, expand=True), k.text(b, size=13, weight=ft.FontWeight.W_600)]))
    for note in (drd_alchymie.sphere_note(it), drd_alchymie.craft_problem(c, it)):
        if note:
            body.append(k.text(note, size=13, color=l.warn))
    mags = it["mags"]

    def make(e):
        def do(v):
            spent = max(0, int(v.get("mana") or 0))
            if spent > int(c.get("mana", 0)) or it["raw"] > int(c.get("raw", 0)):
                app.toast("Nemáš dost magenergie nebo surovin.")
                return
            c["mana"] = int(c.get("mana", 0)) - spent
            c["raw"] = int(c.get("raw", 0)) - it["raw"]
            chance = drd_alchymie.success_chance(c["attrs"][1])
            roll = d(100)
            ok, special = drd.pct_outcome(roll, chance, c["level"])
            txt = drd.pct_text(roll, chance, c["level"])[1]
            if ok:
                cat = "Lektvar" if it["group"] in ("Lektvary", "Jedy") else "Ostatní"
                c.setdefault("items", []).append(model.item(it["name"], cat, info=it["desc"]))
            model.add_history(c, f"Výroba: {it['name']}", txt)
            app.save(c)
            spell_result.show(app, c, it["name"], spent, ok, roll, chance,
                              word=special.capitalize() if special else None,
                              note=("Předmět je v batohu." if ok else
                                    f"Výroba se nepovedla. Magenergie i suroviny ({it['raw']} zl) se spotřebovaly."))
        app.close_dialog()
        app.form(f"Vyrobit: {it['name']}", [("mana", f"Magenergie ({it['mana']})", mags or 0, "int")], do,
                 save_label="Vyrobit a hodit k%")

    app.page.show_dialog(ft.AlertDialog(
        title=k.text(it["name"], size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column(body, spacing=6, tight=True, scroll=ft.ScrollMode.AUTO), width=380),
        actions=[ft.TextButton("Vyrobit", on_click=make, disabled=drd_alchymie.craft_problem(c, it) is not None),
                 ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())], scrollable=True))
