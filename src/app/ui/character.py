"""Obrazovky postavy: přehled, postup na úroveň, dovednosti / schopnosti."""
from __future__ import annotations

import copy

import flet as ft

from .. import model
from ..rules import dh, dh_vybava, drd, drd_kouzla, drd_obory
from ..rules.common import d, fmt
from . import avatar as avatar_ui
from . import companions as comp_ui
from . import druzina, magic, sheet
from .kit import column


def postava(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"

    avatar = level_avatar(app, c)
    nxt = model.xp_next(c)
    if nxt and c.get("xp_next") != nxt:
        c["xp_next"] = nxt
    xp = f"Zkušenosti {c['xp']}" + (f" / {nxt}" if nxt else "")
    if model.can_level_up(c):
        xp += " · můžeš postoupit!"
    up = ft.Container(ft.Icon(ft.Icons.TRENDING_UP, size=24, color=l.orn), width=46, height=46,
                      alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(l.radius),
                      gradient=k.grad(l.card2, l.card), border=ft.Border.all(1, l.orn), shadow=k.glow(10),
                      on_click=lambda e: open_postup(app), ink=True, tooltip="Postup na vyšší úroveň", data="postup")
    header = ft.Row([
        avatar,
        ft.Column([
            k.text(c["name"], size=21, weight=ft.FontWeight.BOLD, head=True, max_lines=2),
            k.text(f"{c['race']} · {magic.branch_label(c)}", size=14),
            ft.Container(ft.Row([ft.Icon(ft.Icons.STAR_OUTLINE, size=15, color=l.orn), k.muted(xp + " ⓘ", size=12)],
                                spacing=6, tight=True),
                         on_click=lambda e: sheet.xp_table_dialog(app, c), tooltip="Tabulka zkušeností"),
        ], spacing=2, expand=True),
        ft.Container(up, padding=ft.Padding.only(bottom=8)),
    ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.END)

    def change_hp(sign: int):
        def save(v):
            n = int(v["n"])
            c["hp"] = max(c.get("death", 0) if is_dh else -99, min(c["hp_max"], c["hp"] + sign * n))
            model.add_history(c, "Zranění" if sign < 0 else "Léčení", f"{'−' if sign < 0 else '+'}{n}")
            app.save(c)
            app.refresh()
        app.form("Zranění" if sign < 0 else "Léčení", [("n", "Počet životů", 1, "int")], save,
                 save_label="Potvrdit")

    def change_mana(sign: int):
        def save(v):
            c["mana"] = max(0, min(c["mana_max"], c["mana"] + sign * int(v["n"])))
            app.save(c)
            app.refresh()
        app.form(f"{c.get('mana_name') or 'Mana'}: {'utratit' if sign < 0 else 'doplnit'}",
                 [("n", "Množství", 1, "int")], save, save_label="Potvrdit")

    def rest(e):
        if is_dh:
            c["mana"] = c["mana_max"]
            app.toast("Mana doplněna na maximum.")
        else:
            c["hp"] = min(c["hp_max"], c["hp"] + 2)
            msg = "Odpočinek: +2 životy"
            if c.get("mana_max") and c["cls"] != "Alchymista" and c.get("mana", 0) < c["mana_max"]:
                c["mana"] = c["mana_max"]
                msg += ", magenergie doplněna (po vyspání)"
            app.toast(msg + ".")
        app.save(c)
        app.refresh()

    if model.sync_mana(c):
        app.save(c)
    show_mana = c.get("mana_max", 0) > 0 or model.uses_mana(c)
    hp_extra = (f" · hr. smrti {c['death']}" if is_dh else
                f" · vyřazení při {drd.knockout_limit(c['hp_max'], c['attrs'][2])}")
    gauges: list[ft.Control] = [k.gauge("Životy", c["hp"], c["hp_max"], l.hp, hp_extra)]
    st = model.status(c)
    if st:
        gauges.append(ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=getattr(l, st[1]), size=18),
                              k.text(st[0], size=13, weight=ft.FontWeight.W_600, color=getattr(l, st[1]))],
                             spacing=6))
    if show_mana:
        gauges.append(k.gauge(c.get("mana_name") or "Mana", c["mana"], c["mana_max"], l.mana))
    btn_row = [k.button("Zranit", lambda e: change_hp(-1), primary=False, expand=1, height=44),
               k.button("Léčit", lambda e: change_hp(+1), primary=False, expand=1, height=44),
               k.button("Odpočinek", rest, primary=False, expand=1, height=44)]
    gauges.append(ft.Row(btn_row, spacing=8))
    if c["cls"] == "Alchymista":
        raw = int(c.get("raw", 0))

        def adj_raw(delta):
            def h(e):
                c["raw"] = max(0, int(c.get("raw", 0)) + delta)
                app.save(c)
                app.refresh()
            return h
        gauges.append(k.stepper(raw, adj_raw(-5), adj_raw(+5), label="Suroviny",
                                sub=(f"na začátku hry {c.get('raw_max', 0)} · po 5" if is_dh
                                     else "zlaťáky v truhle · po 5")))
    if is_dh:
        fat = int(c.get("fatigue", 0))
        fname, fpen = dh.fatigue_state(fat, c["attrs"])

        def adj_fat(delta):
            def h(e):
                c["fatigue"] = max(0, int(c.get("fatigue", 0)) + delta)
                app.save(c)
                app.refresh()
            return h
        gauges.append(k.stepper(fat, adj_fat(-1), adj_fat(+1), label=f"Body únavy · {fname}",
                                sub=f"hranice únavy {dh.fatigue_limit(c['attrs'])}" + (f" · postih {fpen}" if fpen else ""),
                                value_color=l.bad if fpen else None))
    if show_mana:
        gauges.append(ft.Row([k.button(f"− {c.get('mana_name') or 'Mana'}", lambda e: change_mana(-1), primary=False,
                                       expand=1, height=40),
                              k.button(f"+ {c.get('mana_name') or 'Mana'}", lambda e: change_mana(+1), primary=False,
                                       expand=1, height=40)], spacing=8))

    attrs = ft.Row([
        k.stat(a, c["attrs"][i], fmt(r.bonus(c["attrs"][i])),
               sub_color=(l.accent2 if is_dh else l.orn) if r.bonus(c["attrs"][i]) > 0 else l.muted)
        for i, a in enumerate(r.ATTRS)
    ], spacing=6)

    ratio = model.load_ratio(c)
    if is_dh:
        info = (f"Velikost {model.size(c)} · pohyblivost {dh.movement(c['race'], c['attrs'], ratio)} sáhů/kolo"
                f" · nosnost {c.get('capacity', 0):g} lb")
    else:
        obj, mech = drd.perception(c["race"], c["attrs"])
        info = (f"Velikost {model.size(c)} · pohyblivost {drd.movement(c['race'], c['attrs'], ratio)} "
                f"(základ {drd.base_movement(c['race'], c['attrs'])}) · postřeh objekty {obj} %, mechanismy {mech} %")
        al = drd.alignment(c.get("alignment"))
        if al:
            info += f" · přesvědčení {al[1].lower()}"
    extra: list[ft.Control] = []
    sp = drd.race_special(c["race"]) if not is_dh else None
    if sp:
        extra.append(ft.Row([ft.Icon(ft.Icons.VISIBILITY_OUTLINED, size=16, color=l.orn),
                             k.text(f"{sp[0]}: ", size=13, weight=ft.FontWeight.BOLD),
                             k.muted(f"{sp[1]} ({sp[2]})", size=12, expand=True)],
                            spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    attrs = ft.Column([attrs, k.muted(info, size=12), *extra], spacing=6)

    # boj
    fight_rows: list[ft.Control] = []
    pen, why = model.combat_penalty(c)
    for wi, w in enumerate(model.weapons(c)):
        uc = model.uc(c, w)
        ocv = model.oc(c, w)
        stats = (f"útočnost {w.get('attack', 0)} · zranění {fmt(int(w.get('damage', 0)))} · obrana {w.get('defense', 0)}"
                 if is_dh else f"SZ {w.get('attack', 0)} · útočnost {fmt(int(w.get('damage', 0)))} · "
                               f"OZ {fmt(int(w.get('defense', 0)))}")
        if model.is_racial(c, w):
            stats += " · rodová zbraň +1 ÚČ"
        if not is_dh and w.get("ranged") and w.get("range"):
            m, st_, v = w["range"]
            stats += f" · dostřel {m}/{st_}/{v} sáhů: ÚČ {uc + 1}/{uc}/{uc - 1}"
        fight_rows.append(ft.Container(ft.Row([
            ft.Column([k.text(w["name"], size=18, weight=ft.FontWeight.BOLD, head=True, color=l.ptext),
                       k.muted(stats + (" · střelná" if w.get("ranged") else ""), size=14, color=l.pmuted)],
                      spacing=2, expand=True),
            ft.Container(k.stat("ÚČ", uc), width=56),
            ft.Container(k.stat("OČ" if is_dh else "OBRANA", ocv), width=56 if is_dh else 72),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color=l.accent),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=lambda e, wi=wi: app.go("kostky", dice_tab="Souboj", dice_weapon=wi), ink=True,
            tooltip="Kostky → Souboj s touto zbraní", data=f"weapon:{wi}"))
    for wtxt in model.warnings(c):
        fight_rows.append(k.text(wtxt, size=13, color=l.pwarn, weight=ft.FontWeight.BOLD))
    if pen:
        fight_rows.append(k.text(f"Postih k útoku i obraně {pen} ({', '.join(why)})", size=13,
                                 weight=ft.FontWeight.BOLD, color=l.pbad))
    arm = model.armor_quality(c)
    shield = model.shield_bonus(c)
    if is_dh:
        fight_rows.append(k.muted(color=l.pmuted, value=f"ZO {dh.base_defense(c['attrs'], arm)} (OBR + zbroj {arm}) · štít {fmt(shield)} · "
                                  f"iniciativa OBR {fmt(dh.bonus(c['attrs'][1]))} + k6"))
    else:
        fight_rows.append(k.muted(color=l.pmuted, value=f"OČ {model.oc_sheet(c)} (kvalita zbroje {arm} + OBR "
                                  f"{fmt(drd.bonus(c['attrs'][1]))}) · obrana = OČ + OZ zbraně + štít {fmt(shield)} · "
                                  f"útok ÚČ + k6+, obrana + k6+"))

    # dovednosti (DH) / schopnosti povolání a vlastní dovednosti (DrD)
    skills_block: list[ft.Control] = []
    if is_dh:
        skills = sorted(c["skills"], key=lambda s: -s["level"])[:5]
        srows = [k.row_item(s["name"], f"{s['attr']} · stupeň {s['level']}",
                            badge="VLASTNÍ" if s.get("kind") == "Vlastní" else None,
                            on_click=lambda e, s=s: app.go("kostky", dice_tab="Dovednost", dice_skill=s["name"]))
                 for s in skills]
        skills_block = [k.section("Dovednosti", ft.TextButton("Upravit", on_click=lambda e: app.go("dovednosti")),
                                  icon=ft.Icons.HISTORY_EDU),
                        k.list_card(srows) if srows else k.empty("Zatím žádné. Přidej je přes „Upravit“.")]
    class_block: list[ft.Control] = []
    if not is_dh:
        branch = c.get("branch")
        pick_branch: list[ft.Control] = []
        if c["level"] >= drd_obory.ADV_LEVEL and not branch and drd_obory.BRANCHES.get(c["cls"]):
            pick_branch = [k.button("Zvolit obor (6. úroveň)", lambda e: app.go("obor"), primary=False,
                                    icon=ft.Icons.ALT_ROUTE, height=44)]
        note = drd.class_note(c["cls"]) if c["cls"] in drd.CLASS_FEATURES else ""
        if c["level"] > drd.MAX_TABLE_LEVEL and c["cls"] == "Zloděj" and branch not in ("Lupič", "Sicco"):
            note += " Tabulky PPZ končí 5. úrovní, používají se hodnoty pro 5. úroveň."
        if c["level"] >= drd_obory.ADV_LEVEL and branch:
            note += f" Schopnosti oboru {branch} podle Pravidel pro pokročilé – podrobnosti v pravidlech."
        class_block = [k.section("Schopnosti povolání",
                                 plus_circle(app, lambda e: edit_ability(app, None), "Přidat vlastní dovednost"),
                                 icon=ft.Icons.AUTO_AWESOME),
                       *pick_branch,
                       class_abilities_card(app, c["cls"], c["level"], c["attrs"], roll=True, branch=branch,
                                            custom=c),
                       *([k.muted(note.strip(), size=12)] if note.strip() else [])]
    spell_block = magic.spells_section(app, c)
    if c.get("active") or model.uses_mana(c):
        spell_block += magic.active_section(app, c)
    pets = comp_ui.companion_cards(app, c) if not is_dh else []
    pal = (k.link("Společník", lambda e: comp_ui.open_picker(app, c)) if comp_ui.kind_for(c) else None)

    controls = [
        k.card(ft.Column(gauges, spacing=10)),
        druzina.status_card(app, c),
        k.section("Vlastnosti", pal, icon=ft.Icons.AUTO_AWESOME),
        attrs,
        *pets,
        k.section("Boj", icon=ft.Icons.SPORTS_KABADDI),
        k.parch(ft.Column(fight_rows, spacing=10)),
        k.muted("Klepnutím na zbraň se otevřou Kostky → Souboj s touto zbraní.", size=12),
        *class_block,
        *spell_block,
        *skills_block,
    ]
    actions = [ft.IconButton(ft.Icons.PRINT_OUTLINED, icon_color=l.ink, tooltip="Tisk / export listu postavy",
                             on_click=lambda e: sheet.export_sheet(app, c)),
               ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color=l.ink, tooltip="Upravit postavu",
                             on_click=lambda e: edit_character(app))]
    body = [banner(app, header), *[ft.Container(x, padding=ft.Padding.symmetric(horizontal=16)) for x in controls]]
    return Screen(r.NAME, [column(body, padding=0)], actions=actions)


def level_avatar(app, c: dict) -> ft.Control:
    """Portrét postavy vysunutý do ilustrace s kroužkem aktuální úrovně dole."""
    k = app.kit
    l = app.look
    av = avatar_ui.avatar(app, c, 92, 46, l.orn, l.card2, border=3, font_family=k.hf,
                          on_click=lambda e: avatar_ui.avatar_menu(app, c))
    badge = ft.Container(
        k.text(str(c["level"]), size=17, weight=ft.FontWeight.BOLD, head=True, color="#ffffff"),
        width=36, height=36, alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(18),
        gradient=ft.RadialGradient(colors=[l.accent2, l.accent]), border=ft.Border.all(2, l.orn),
        shadow=[ft.BoxShadow(blur_radius=0, spread_radius=3, color=l.bg), ft.BoxShadow(blur_radius=12, color=l.glow)],
        tooltip=f"{c['level']}. úroveň", data="level-badge")
    return ft.Stack([ft.Container(av, left=0, top=0), ft.Container(badge, left=28, bottom=0)], width=92, height=110,
                    clip_behavior=ft.ClipBehavior.NONE)


def _abbr(app, code: str, on: bool = False) -> ft.Control:
    l = app.look
    return ft.Container(app.kit.text(code, size=13, weight=ft.FontWeight.BOLD, head=True,
                                     color="#ffffff" if on else l.orn, align=ft.TextAlign.CENTER),
                        width=46, padding=ft.Padding.symmetric(vertical=3), bgcolor=l.accent if on else None,
                        border=ft.Border.all(1, l.orn), border_radius=ft.BorderRadius.all(4),
                        alignment=ft.Alignment.CENTER)


def alignment_card(app, c: dict) -> ft.Control:
    """Přesvědčení pod jménem postavy (DrD 1.6, podle grafického návrhu)."""
    k = app.kit
    l = app.look
    a = drd.alignment(c.get("alignment"))
    name, desc, code = (a[1], a[2], a[0]) if a else ("Nezvoleno", "Klepni na tužku – vyber, nebo hoď k10 podle rasy.",
                                                      "–")
    return k.framed(ft.Row([
        ft.Icon(ft.Icons.BALANCE, size=26, color=l.orn),
        ft.Column([k.text("PŘESVĚDČENÍ", size=11, weight=ft.FontWeight.BOLD, color=l.muted),
                   k.text(name, size=19, weight=ft.FontWeight.BOLD, head=True),
                   k.muted(desc, size=13)], spacing=2, expand=True),
        _abbr(app, code),
        k.square_button(ft.Icons.EDIT_OUTLINED, lambda e: alignment_dialog(app, c), "Změnit přesvědčení"),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=12), glow=True, on_click=lambda e: alignment_dialog(app, c))


def alignment_dialog(app, c: dict) -> None:
    """Výběr přesvědčení, nebo hod k10 podle tabulky pro rasu postavy."""
    from . import dice_shapes

    k = app.kit
    l = app.look
    st = {"sel": c.get("alignment"), "roll": None}
    table = drd.ALIGN_TABLE.get(c["race"], drd.ALIGN_TABLE["Člověk"])
    holder = ft.Column(spacing=10, tight=True)

    def pick(code):
        def h(e):
            st["sel"] = code
            draw()
        return h

    def roll(e):
        st["roll"], st["sel"] = drd.roll_alignment(c["race"])
        draw()

    def draw():
        opts = []
        for code, name, desc in drd.ALIGNMENTS:
            on = code == st["sel"]
            opts.append(ft.Container(ft.Row([
                _abbr(app, code, on),
                ft.Column([k.text(name, size=15, weight=ft.FontWeight.BOLD), k.muted(desc, size=12)], spacing=1,
                          expand=True),
                ft.Icon(ft.Icons.CHECK, size=20, color=l.ok) if on else ft.Container(width=20),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10), border_radius=ft.BorderRadius.all(l.radius),
                gradient=k.grad(l.card2, l.card) if on else None, bgcolor=None if on else l.card,
                border=ft.Border.all(2 if on else 1, l.orn if on else l.border), shadow=k.glow(12) if on else None,
                on_click=pick(code), ink=True, data="align:" + code))
        r = st["roll"]
        sel_name = (drd.alignment(st["sel"]) or ("", "–"))[1]
        cells = [ft.Container(ft.Column([
            k.text(str(i + 1), size=11, color="#ffffff" if r == i + 1 else l.muted, align=ft.TextAlign.CENTER),
            k.text(v, size=11, weight=ft.FontWeight.BOLD, color="#ffffff" if r == i + 1 else None,
                   align=ft.TextAlign.CENTER)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=1, padding=ft.Padding.symmetric(vertical=4), border_radius=ft.BorderRadius.all(4),
            bgcolor=l.accent if r == i + 1 else None, shadow=k.glow(8) if r == i + 1 else None)
            for i, v in enumerate(table)]
        roll_card = k.framed(ft.Column([
            ft.Row([dice_shapes.die(app, "10", str(r) if r else None, 58, sel=bool(r)),
                    ft.Column([k.muted(f"Hod k10 podle rasy · {c['race']}", size=12),
                               k.text(f"Padlo {r} → {sel_name}" if r else "Zatím nehozeno", size=17,
                                      weight=ft.FontWeight.BOLD, head=True)], spacing=2, expand=True)],
                   spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Row(cells, spacing=2),
            k.button("Hodit k10 podle rasy", roll, primary=False, icon=ft.Icons.CASINO_OUTLINED, height=44),
        ], spacing=10), padding=12)
        holder.controls = [
            ft.Row([ft.Icon(ft.Icons.BALANCE, size=24, color=l.orn),
                    k.text("Přesvědčení", size=21, weight=ft.FontWeight.BOLD, head=True)], spacing=10),
            k.muted("Vyber sám, nebo hoď k10 – tabulka podle rasy postavy. Zákonné dobro → zákonné zlo.", size=13),
            ft.Column(opts, spacing=6),
            roll_card,
        ]
        try:
            app.page.update()
        except Exception:
            pass

    def save(e):
        app.close_dialog()
        if st["sel"]:
            c["alignment"] = st["sel"]
            if st["roll"]:
                model.add_history(c, "Přesvědčení k10", f"{st['roll']} · {st['sel']}")
            app.save(c)
            app.refresh()

    draw()
    app.page.show_dialog(ft.AlertDialog(
        content=ft.Container(ft.Column([holder], tight=True, scroll=ft.ScrollMode.AUTO), width=360), bgcolor=l.card,
        actions=[ft.TextButton("Zrušit", on_click=lambda e: app.close_dialog()),
                 ft.FilledButton(content=ft.Row([ft.Icon(ft.Icons.CHECK, size=18), ft.Text("Uložit")], tight=True,
                                                spacing=6),
                                 on_click=save, style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))]))


def banner(app, header: ft.Control) -> ft.Control:
    """Ilustrace v záhlaví postavy (drak nad hradem) a přes její spodní okraj portrét se jménem."""
    l = app.look
    if not l.banner:
        return ft.Container(header, padding=ft.Padding.symmetric(horizontal=16))
    return ft.Stack([
        ft.Image(src=l.banner, fit=ft.BoxFit.COVER, height=128, left=0, right=0, top=0, opacity=0.9),
        ft.Container(height=130, left=0, right=0, top=0,
                     gradient=ft.LinearGradient(begin=ft.Alignment.TOP_CENTER, end=ft.Alignment.BOTTOM_CENTER,
                                                colors=["#00000000", l.bg], stops=[0.3, 0.97])),
        ft.Container(header, left=16, right=16, bottom=0),
    ], height=200)


def edit_character(app) -> None:
    c = app.char
    fields = [("name", "Jméno", c["name"], "text"), ("race", "Rasa", c["race"], "text"),
              ("cls", "Povolání", c["cls"], "text"), ("xp", "Zkušenosti", c["xp"], "int"),
              ("xp_next", "Zkušenosti na další úroveň", c.get("xp_next", 0), "int"),
              ("hp", "Aktuální životy", c["hp"], "int"),
              ("mana_name", "Název many (Mana, Adrenalin, Magenergie…)", c.get("mana_name", ""), "text"),
              ("mana", "Aktuální mana", c["mana"], "int"), ("mana_max", "Maximum many", c["mana_max"], "int")]
    if c["system"] == "dh":
        fields.append(("death", "Hranice smrti", c["death"], "int"))

    def save(v):
        c.update(v)
        c["hp"] = min(c["hp"], c["hp_max"])
        c["mana"] = min(c["mana"], c["mana_max"])
        app.save(c)
        app.refresh()
    app.form("Upravit postavu", fields, save)


# --- postup na úroveň ----------------------------------------------------------

def open_postup(app) -> None:
    c = app.char
    app.ui["lvl"] = {"level": c["level"] + 1, "hp_max": c["hp_max"], "mana_max": c["mana_max"],
                     "attrs": list(c["attrs"]), "skill_points": c.get("skill_points", 0),
                     "xp_next": c.get("xp_next", 0), "rolled": None, "branch": c.get("branch"),
                     "dog_roll": None, "dog": None}
    w = app.ui["lvl"]
    w["xp_next"] = model.xp_next({**c, "level": c["level"] + 1}) or 0
    if c["system"] == "drd":
        table = drd.class_mana(c["cls"], c["level"] + 1, c["attrs"], c.get("branch"))
    else:
        table = dh.class_mana(c["cls"], c["level"] + 1, c["attrs"])
        w["skill_points"] = c.get("skill_points", 0) + dh.SKILL_POINTS.get(c["cls"], 3) * (c["level"] + 1)
        w["attr_up"] = []
    if table:
        w["mana_max"] = max(c["mana_max"], table)
    app.go("postup")


def roll_button(app, title: str, sub: str, on_click) -> ft.Control:
    """Velké tlačítko hodu s malým popiskem (např. „k10 + oprava odolnost“)."""
    k = app.kit
    l = app.look
    return ft.Container(ft.Row([
        ft.Icon(ft.Icons.CASINO_OUTLINED, size=26, color=l.on_accent),
        ft.Column([k.text(title, size=16, weight=ft.FontWeight.BOLD, head=True, color=l.on_accent),
                   k.text(sub, size=12, color=l.on_accent)], spacing=1, expand=True),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=12), border_radius=ft.BorderRadius.all(l.radius),
        gradient=k.grad(l.accent2, l.accent), border=ft.Border.all(1, l.orn), shadow=k.glow(14),
        on_click=on_click, ink=True, data="roll-hp")


def ask_backup(app, on_yes) -> None:
    """Před hodem při postupu: „Zálohoval jsi deník?“ ANO hází, NE nic nedělá."""
    k = app.kit
    l = app.look

    def yes(e):
        app.close_dialog()
        on_yes()
    app.page.show_dialog(ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.Icons.DOWNLOAD, size=24, color=l.orn),
                      k.text("Zálohoval jsi deník?", size=20, weight=ft.FontWeight.BOLD, head=True)], spacing=10),
        content=ft.Container(k.muted("Hod na životy a magenergii změní postavu. Když nemáš zálohu, klepni na NE, "
                                     "zálohuj na obrazovce Moje postavy a pak se vrať.", size=13), width=340),
        bgcolor=l.card,
        actions=[ft.TextButton("NE", on_click=lambda e: app.close_dialog()),
                 ft.FilledButton(content=ft.Text("ANO"), on_click=yes,
                                 style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))]))


def postup(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"
    w = app.ui.setdefault("lvl", None)
    if w is None:
        open_postup(app)
        w = app.ui["lvl"]

    def adj(key, delta, lo=0):
        def h(e):
            w[key] = max(lo, w[key] + delta)
            app.refresh()
        return h

    def adj_attr(i, delta):
        def h(e):
            w["attrs"][i] = max(1, w["attrs"][i] + delta)
            app.refresh()
        return h

    def diff(new, old):
        return "beze změny" if new == old else f"{old} – {new}"

    rows = [
        k.stepper(w["level"], adj("level", -1, 1), adj("level", +1), label="Úroveň", sub=diff(w["level"], c["level"])),
        k.stepper(w["hp_max"], adj("hp_max", -1, 1), adj("hp_max", +1), label="Maximum životů",
                  sub=diff(w["hp_max"], c["hp_max"])),
        k.stepper(w["mana_max"], adj("mana_max", -1), adj("mana_max", +1),
                  label=f"Maximum: {c.get('mana_name') or 'mana'}", sub=diff(w["mana_max"], c["mana_max"])),
    ]
    need = model.xp_next({**c, "level": w["level"] - 1})
    if need:
        cost = drd.training_cost(c["cls"], w["level"]) if not is_dh else None
        rows.append(k.muted(f"Na {w['level']}. úroveň je potřeba {need} zkušeností (máš {c['xp']})" +
                            (f" · výcvik stojí {cost} zl" if cost else ""), size=13,
                            color=l.ok if c["xp"] >= need else l.warn))
    if is_dh:
        rows.append(k.stepper(w["skill_points"], adj("skill_points", -1), adj("skill_points", +1),
                              label="Dovednostní body",
                              sub=f"+{dh.SKILL_POINTS.get(c['cls'], 3)}× úroveň podle Tabulky dovednostních bodů"))

        def roll_hp_dh(fixed):
            def h(e):
                kk, gain = dh.level_hp_roll(c["attrs"], fixed=fixed)
                w["hp_max"] += gain
                w["rolled"] = (f"{'pevně 3' if fixed else f'k6 = {kk}'} {fmt(dh.bonus(c['attrs'][2]))} ODO – +{gain}")
                app.refresh()
            return h
        rows.append(ft.Row([k.button("Hodit 1k6 + ODO na životy", roll_hp_dh(False), primary=False, expand=1,
                                     icon=ft.Icons.CASINO_OUTLINED),
                            k.button("Průměr 3 + ODO", roll_hp_dh(True), primary=False, expand=1)], spacing=8))
        if w.get("rolled"):
            rows.append(k.muted(f"Přírůstek: {w['rolled']}"))
        table = dh.class_mana(c["cls"], w["level"], c["attrs"])
        if table is not None and c["cls"] != "Alchymista":
            def use_dh_table(e, table=table):
                w["mana_max"] = table
                app.refresh()
            rows.append(ft.Row([
                k.muted(f"Tabulka ({c.get('mana_name') or 'mana'}): {table}" +
                        (" – tabulka končí 6. úrovní" if w["level"] > 6 else ""), size=13, expand=True),
                ft.TextButton("Použít", on_click=use_dh_table)]))
        if dh.attr_up_level(w["level"]):
            banner = (f"{w['level']}. úroveň: získáváš 2 charakterové body – zvyš dva různé atributy o 1 (vyber níže). "
                      "Změna opravy za Odolnost přepočítá životy i hranici smrti.")
        else:
            banner = "Každou dovednost lze za úroveň zlepšit nejvýš o jeden stupeň. Zlepšení atributů je na každé třetí úrovni."
    else:
        cls = c["cls"] if c["cls"] in drd.HP_TABLE else "Válečník"
        _, sides, add = drd.HP_TABLE[cls]

        table = drd.class_mana(c["cls"], w["level"], c["attrs"], w.get("branch") or c.get("branch"))
        undo = w.setdefault("undo", [])

        def remember():
            undo.append({"hp_max": w["hp_max"], "mana_max": w["mana_max"], "rolled": w.get("rolled")})

        def roll_hp():
            remember()
            kk, gain = drd.level_hp_roll(cls, c["attrs"])
            w["hp_max"] += gain
            w["rolled"] = f"k{sides} = {kk}{fmt(add) if add else ''} {fmt(drd.bonus(c['attrs'][2]))} ODL – +{gain}"
            if table is not None and c["cls"] != "Alchymista":
                w["mana_max"] = max(w["mana_max"], table)
                w["rolled"] += f" · magenergie {w['mana_max']}"
            app.refresh()

        def fixed_hp():
            remember()
            gain = drd.HP_FIXED.get(cls, 1)
            w["hp_max"] += gain
            w["rolled"] = f"pevný přírůstek od 10. úrovně – +{gain}"
            if table is not None and c["cls"] != "Alchymista":
                w["mana_max"] = max(w["mana_max"], table)
            app.refresh()

        def take_back(e):
            if not undo:
                app.toast("Není co vrátit.")
                return
            w.update(undo.pop())
            app.refresh()

        fixed = w["level"] >= drd.HP_FIXED_LEVEL
        rows.append(roll_button(
            app, "Hod na životy a magenergii",
            (f"pevně +{drd.HP_FIXED.get(cls, 1)} (od 10. úrovně)" if fixed else
             f"k{sides}{fmt(add) if add else ''} + oprava odolnost"),
            lambda e: ask_backup(app, fixed_hp if fixed else roll_hp)))
        back_btn = k.button("Zpět – vrátit poslední hod", take_back, primary=False, icon=ft.Icons.UNDO, height=44,
                            disabled=not undo)
        back_btn.data = "undo-roll"
        rows.append(back_btn)
        if w.get("rolled"):
            rows.append(k.muted(f"Hod: {w['rolled']}"))
        if table is not None:
            br = w.get("branch") or c.get("branch")
            if magic.is_wizard(c):
                extra = f" · počet kouzel {drd_kouzla.spell_count(w['level'])}"
            elif w["level"] >= 6 and not br:
                extra = " – po volbě oboru se použije tabulka oboru"
            elif c["cls"] == "Alchymista" and w["level"] > 9:
                extra = " (tabulka končí 9. úrovní, dál alchymista destiluje sám)"
            elif w["level"] > 15:
                extra = " (tabulka končí 15. úrovní)"
            else:
                extra = f" ({br})" if br and w["level"] >= 6 else ""
            rows.append(k.muted(f"Tabulka magenergie: {table} magů{extra}", size=13))
        has_dog = any(x.get("kind") == "pes" for x in c.get("companions", []))
        if c["cls"] == "Hraničář" and not has_dog and w["level"] > c["level"]:
            def roll_dog(e):
                r = d(100)
                dog = drd_obory.dog_for_roll(r)
                w["dog_roll"] = r
                w["dog"] = dog["name"] if dog else None
                app.refresh()
            rows.append(k.button(f"Hodit k% na psa (šance {drd_obory.DOG_CHANCE} %)", roll_dog, primary=False,
                                 icon=ft.Icons.PETS))
            if w.get("dog_roll") is not None:
                rows.append(k.muted(f"Padlo {w['dog_roll']}: " + (f"{w['dog']} – přidá se po uložení."
                                                                    if w.get("dog") else "pes tentokrát není.")))
        if c["level"] > 1:
            def drain(e):
                def yes():
                    from ..rules import drd_pj
                    txt = drd_pj.drain_level(c)
                    if txt:
                        model.add_history(c, "Ztráta úrovně", txt)
                        app.save(c)
                        app.ui["lvl"] = None
                        app.toast(txt)
                        app.go("postava")
                app.confirm("Postava ztratila úroveň?",
                            "Třeba dotykem nemrtvého. Úroveň klesne o 1, zkušenosti na 1 méně, než je potřeba "
                            "na ztracenou úroveň. Kouzla, životy a dovednosti zůstávají; hody podle nižší úrovně.",
                            yes, yes_label="Snížit úroveň")
            rows.append(ft.TextButton("Postava ztratila úroveň…", on_click=drain, icon=ft.Icons.TRENDING_DOWN))
        banner = ("Vlastnosti se v DrD 1.6 při postupu běžně nemění. Ruční úprava je pro případy, kdy to povolí PJ "
                  "(kouzlo, lektvar, kletba). Přírůstek životů je vždy alespoň 1.")

    attr_block: list[ft.Control] = []
    if is_dh and dh.attr_up_level(w["level"]):
        picked = w.setdefault("attr_up", [])

        def toggle_attr(a):
            if a in picked:
                picked.remove(a)
            elif len(picked) < 2:
                picked.append(a)
            else:
                app.toast("Vyber dva různé atributy.")
                return
            i = dh.ATTRS.index(a)
            w["attrs"][i] = c["attrs"][i] + (1 if a in picked else 0)
            app.refresh()
        attr_block = [k.section(f"Charakterové body ({len(picked)}/2)"),
                      ft.Row([k.pill(a, a in picked, lambda e, a=a: toggle_attr(a), expand=1) for a in dh.ATTRS],
                             spacing=6)]

    attr_cells = []
    for i, a in enumerate(r.ATTRS):
        changed = w["attrs"][i] != c["attrs"][i]
        attr_cells.append(ft.Container(ft.Column([
            k.muted(a, size=11, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.Icons.ADD, on_click=adj_attr(i, +1), icon_color=l.ink, tooltip=f"Zvýšit {a}"),
            k.text(w["attrs"][i], size=20, weight=ft.FontWeight.BOLD, head=True, color=l.hi if changed else l.ink),
            ft.IconButton(ft.Icons.REMOVE, on_click=adj_attr(i, -1), icon_color=l.ink, tooltip=f"Snížit {a}"),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0), expand=1, bgcolor=l.card,
            border=ft.Border.all(2 if changed else 1, l.hi if changed else l.border),
            border_radius=ft.BorderRadius.all(l.radius), padding=ft.Padding.symmetric(vertical=6)))

    needs_branch = (not is_dh and w["level"] >= drd_obory.ADV_LEVEL and not c.get("branch")
                    and bool(drd_obory.BRANCHES.get(c["cls"])))

    def pick_branch(n):
        w["branch"] = n
        table = drd.class_mana(c["cls"], w["level"], c["attrs"], n)
        if table:
            w["mana_max"] = max(c["mana_max"], table)
        app.refresh()

    def save(e):
        if needs_branch and not w.get("branch"):
            app.toast("Na 6. úrovni si vyber obor povolání.")
            return
        if needs_branch:
            c["branch"] = w["branch"]
            model.add_history(c, "Obor", w["branch"])
        if w.get("dog"):
            c.setdefault("companions", []).append({"id": model.new_id(), "kind": "pes", "name": w["dog"], "nick": "",
                                                   "since": w["level"], "overrides": {}, "note": ""})
        gain = w["hp_max"] - c["hp_max"]
        old_odo = c["attrs"][2]
        c["level"] = w["level"]
        c["hp_max"] = w["hp_max"]
        c["hp"] = max(-99, min(c["hp_max"], c["hp"] + max(0, gain)))
        c["mana_max"] = w["mana_max"]
        c["mana"] = min(c["mana"], c["mana_max"])
        c["attrs"] = list(w["attrs"])
        c["xp_next"] = model.xp_next(c) or c.get("xp_next", 0)
        if is_dh:
            c["skill_points"] = w["skill_points"]
            d_bonus = dh.bonus(c["attrs"][2]) - dh.bonus(old_odo)
            if d_bonus:
                # životy = 10 + ODO + přírůstky (k6 + ODO na každé úrovni) → změna opravy působí na každou úroveň
                c["hp_max"] = max(1, c["hp_max"] + d_bonus * c["level"])
                c["hp"] = min(c["hp_max"], c["hp"] + max(0, d_bonus * c["level"]))
            if c["attrs"][2] != old_odo:
                c["death"] = dh.death_threshold(c["attrs"])
            c["capacity"] = float(dh_vybava.carry_capacity(dh.bonus(c["attrs"][0])))
        model.add_history(c, "Postup", f"{c['level']}. úroveň")
        app.save(c)
        app.ui["lvl"] = None
        app.toast(f"Uloženo: {c['level']}. úroveň")
        app.go("postava")

    branch_block: list[ft.Control] = []
    if needs_branch:
        branch_block = [k.section("Volba oboru (Pravidla pro pokročilé)"),
                        k.muted("Na 6. úrovni se postava rozhodne pro jeden ze dvou oborů. Dosavadní schopnosti "
                                "zůstávají, přibudou schopnosti oboru.", size=13),
                        *magic.branch_cards(app, c, w.get("branch"), pick_branch)]
    controls = [
        k.card(k.text(banner, size=14), bg=l.card2),
        k.card(ft.Column(rows, spacing=10)),
        *branch_block,
        *attr_block,
        k.section("Vlastnosti"),
        ft.Row(attr_cells, spacing=6),
        k.button("Uložit postup", save),
    ]
    return Screen("Postup na úroveň", [column(controls)])


# --- dovednosti / schopnosti -----------------------------------------------------

def dovednosti(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    rows: list[ft.Control] = []
    if is_dh:
        for s in sorted(c["skills"], key=lambda s: (-s["level"], s["name"])):
            rows.append(k.row_item(
                s["name"], f"{s['attr']} · stupeň {s['level']}", sub=s.get("kind"),
                badge="VLASTNÍ" if s.get("kind") == "Vlastní" else None, on_click=lambda e, s=s: edit_skill(app, s),
                trailing=ft.IconButton(ft.Icons.CASINO_OUTLINED, icon_color=l.hi, tooltip="Hodit",
                                       on_click=lambda e, s=s: app.go("kostky", dice_tab="Dovednost",
                                                                      dice_skill=s["name"]))))
        info = (f"Dovednostní body: {c.get('skill_points', 0)}. Za 1 bod se naučíš novou dovednost na 1. stupeň. "
                "Hod: 1k10 + oprava vlastnosti + stupeň musí překonat obtížnost.")
    else:
        for a in c["abilities"]:
            rows.append(k.row_item(
                a["name"], f"{a['pct']} %", sub=(a.get("kind") or "") + (f" · oprava {a['attr']}" if a.get("attr") else ""),
                badge="VLASTNÍ" if a.get("kind") == "Vlastní" else None, on_click=lambda e, a=a: edit_ability(app, a),
                trailing=ft.IconButton(ft.Icons.CASINO_OUTLINED, icon_color=l.hi, tooltip="Hodit k%",
                                       on_click=lambda e, a=a: app.go("kostky", dice_tab="Schopnost",
                                                                      dice_ability=a["name"]))))
        info = ("Schopnosti povolání (např. zlodějské činnosti, stopování) a vlastní dovednosti podle domácích "
                "pravidel. Hod: k% musí padnout pod šanci nebo na ni.")
    controls = [
        k.card(k.muted(info, size=14)),
        k.list_card(rows) if rows else k.empty("Zatím prázdné."),
    ]
    fab = ft.FloatingActionButton(icon=ft.Icons.ADD, bgcolor=l.accent, foreground_color=l.on_accent,
                                  on_click=lambda e: (edit_skill(app, None) if is_dh else edit_ability(app, None)),
                                  tooltip="Přidat")
    return Screen("Dovednosti" if is_dh else "Schopnosti", [column(controls)], fab=fab)


def edit_skill(app, s: dict | None) -> None:
    c = app.char
    names = list(dh.SKILLS) + ["(vlastní – vyplň název)"]
    fields = [
        ("preset", "Základní dovednost", s["name"] if s and s["name"] in dh.SKILLS else names[-1], "choice", names),
        ("name", "Vlastní název", "" if s is None or s["name"] in dh.SKILLS else s["name"], "text"),
        ("attr", "Vlastnost", s["attr"] if s else "OBR", "choice", dh.ATTRS),
        ("level", "Stupeň", s["level"] if s else 1, "int"),
        ("kind", "Druh", s.get("kind", "Vlastní") if s else "Vlastní", "choice", ["Blízká", "Obecná", "Vlastní"]),
    ]

    def save(v):
        name = v["name"].strip() if v["preset"] == names[-1] else v["preset"]
        if not name:
            app.toast("Vyplň název dovednosti.")
            return
        data = {"name": name, "attr": v["attr"] or "OBR", "level": max(0, int(v["level"])), "kind": v["kind"] or "Vlastní"}
        if s is None:
            if v["preset"] != names[-1] and v["attr"] == "OBR":
                data["attr"] = dh.SKILLS.get(name, "OBR")
            c["skills"].append(data)
            if c.get("skill_points", 0) > 0:
                c["skill_points"] -= 1
        else:
            s.update(data)
        app.save(c)
        app.refresh()

    def delete():
        c["skills"].remove(s)
        app.save(c)
        app.refresh()

    app.form("Nová dovednost" if s is None else "Upravit dovednost", fields, save,
             on_delete=delete if s is not None else None)


def edit_ability(app, a: dict | None) -> None:
    c = app.char
    fields = [
        ("name", "Název", a["name"] if a else "", "text"),
        ("pct", "Šance (%)", a["pct"] if a else 40, "int"),
        ("hint", "", "Dovednost se přidá do tabulky Schopnosti povolání s označením Vlastní dovednost. "
                     "Hází se na ni v Kostkách → Schopnost.", "info"),
        ("attr", "Přičíst 5 × oprava vlastnosti (volitelné)", a.get("attr", "Žádná") if a else "Žádná", "choice",
         ["Žádná"] + drd.ATTRS),
    ]

    def save(v):
        if not v["name"].strip():
            app.toast("Vyplň název.")
            return
        data = {"name": v["name"].strip(), "pct": max(1, min(99, int(v["pct"]))),
                "attr": None if v["attr"] in (None, "Žádná") else v["attr"], "kind": "Vlastní"}
        if a is None:
            c["abilities"].append(data)
        else:
            a.update(data)
        app.save(c)
        app.refresh()

    def delete():
        c["abilities"].remove(a)
        app.save(c)
        app.refresh()

    app.form("Nová vlastní dovednost" if a is None else "Upravit vlastní dovednost", fields, save,
             on_delete=delete if a is not None else None)


def plus_circle(app, on_click, tooltip: str) -> ft.Control:
    """Červené „+“ v kroužku vedle nadpisu oddílu."""
    l = app.look
    return ft.Container(ft.Icon(ft.Icons.ADD, size=18, color="#ffffff"), width=34, height=34,
                        alignment=ft.Alignment.CENTER, border_radius=ft.BorderRadius.all(17),
                        gradient=ft.RadialGradient(colors=[l.accent2, l.accent]), border=ft.Border.all(1, l.orn),
                        shadow=[ft.BoxShadow(blur_radius=10, color=l.glow)], on_click=on_click, ink=True,
                        tooltip=tooltip, data="plus")


def class_abilities_card(app, cls: str, level: int, attrs: list[int], roll: bool = False,
                         branch: str | None = None, custom: dict | None = None, new_at: int | None = None) -> ft.Control:
    """Schopnosti povolání DrD, které postava na dané úrovni má (vyšší se neukazují).
    custom = postava: na konec přidá její vlastní dovednosti. new_at: označí schopnosti nové na této úrovni."""
    k = app.kit
    l = app.look
    rows: list[ft.Control] = []
    for a in drd.class_abilities(cls, level, attrs, branch):
        if a["locked"]:
            continue
        locked = False
        has_pct = a["pct"] is not None
        value = "–" if locked else (f"{a['pct']} %" if has_pct else a["text"])
        trailing = None
        on_click = None
        if roll and has_pct and not locked:
            on_click = lambda e, n=a["name"]: app.go("kostky", dice_tab="Schopnost", dice_ability=n)  # noqa: E731
            trailing = ft.Icon(ft.Icons.CASINO_OUTLINED, color=l.hi, size=22)
        name_row: list[ft.Control] = [k.text(a["name"], size=15, weight=ft.FontWeight.W_600, max_lines=1)]
        if new_at and a["from_level"] == new_at and new_at > 1:
            name_row.append(ft.Container(ft.Text(f"NOVÉ NA {new_at}. ÚR.", size=10, weight=ft.FontWeight.BOLD,
                                                 color=l.orn), border=ft.Border.all(1, l.orn),
                                         border_radius=ft.BorderRadius.all(4),
                                         padding=ft.Padding.symmetric(horizontal=6, vertical=2)))
        rows.append(ft.Container(ft.Row([
            ft.Column([ft.Row(name_row, spacing=6, wrap=True),
                       k.muted(a["sub"], size=12, max_lines=2)],
                      spacing=1, expand=True),
            k.text(value, size=19, weight=ft.FontWeight.BOLD, head=True,
                   color=l.hi if has_pct and not locked else l.muted),
            *([trailing] if trailing else []),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER), on_click=on_click, ink=on_click is not None))
    if custom is not None:
        c = custom
        for a in c["abilities"]:
            rows.append(ft.Container(ft.Row([
                ft.Column([k.text(a["name"], size=15, weight=ft.FontWeight.W_600, max_lines=1),
                           k.text("Vlastní dovednost", size=12, weight=ft.FontWeight.BOLD, color=l.orn)],
                          spacing=1, expand=True),
                k.text(f"{ability_chance(c, a)} %", size=19, weight=ft.FontWeight.BOLD, head=True, color=l.hi),
                ft.IconButton(ft.Icons.CASINO_OUTLINED, icon_color=l.hi, icon_size=22, tooltip="Hodit k%",
                              on_click=lambda e, n=a["name"]: app.go("kostky", dice_tab="Schopnost", dice_ability=n)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=lambda e, a=a: edit_ability(app, a), ink=True, data="custom:" + a["name"],
                tooltip="Upravit vlastní dovednost"))
    if not rows:
        return k.empty("Žádné schopnosti. Vlastní dovednost přidáš tlačítkem +.")
    return k.list_card(rows)


def rollable_abilities(c: dict) -> list[dict]:
    """Všechny schopnosti DrD, na které se hází k%: povolání (podle úrovně) + vlastní."""
    out = [{"name": a["name"], "chance": a["pct"], "kind": "Schopnost povolání"}
           for a in drd.class_abilities(c["cls"], c["level"], c["attrs"], c.get("branch"))
           if a["pct"] is not None and not a["locked"]]
    names = {a["name"] for a in out}
    out += [{"name": a["name"], "chance": ability_chance(c, a), "kind": a.get("kind") or "Vlastní"}
            for a in c["abilities"] if a["name"] not in names]
    return out


def ability_chance(c: dict, a: dict) -> int:
    base = int(a["pct"])
    if a.get("attr") in drd.ATTRS:
        base += 5 * drd.bonus(c["attrs"][drd.ATTRS.index(a["attr"])])
    return max(1, min(99, base))


_ = copy
