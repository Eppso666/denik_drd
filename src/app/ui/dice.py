"""Kostky a souboj. Každá hra má vlastní sadu kostek a vlastní typy hodů."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules import dh, drd
from ..rules.common import d, fmt, open_d6, roll_expr
from .character import rollable_abilities
from . import dice_shapes as shapes
from .kit import column


def _push(app, label: str, value, detail: str, color: str, die: str = "6", head: str | None = None,
          free: bool = False) -> None:
    """Výsledek hodu: uloží se do historie a ukáže v kartě výsledku s tvarem hozené kostky."""
    c = app.char
    app.ui["dice_last"] = {"label": label, "value": str(value), "detail": detail, "color": color,
                           "char": c["id"], "die": die, "head": head, "free": free}
    model.add_history(c, label.capitalize(), str(value))
    app.save(c)
    app.refresh()


def _result_card(app) -> ft.Control:
    """Karta výsledku podle návrhu: vlevo kostka s hozeným číslem, vpravo co a jak to dopadlo."""
    k = app.kit
    l = app.look
    last = app.ui.get("dice_last")
    if not last or last.get("char") != app.char["id"]:
        return k.framed(ft.Row([
            shapes.die(app, "20", None, 96),
            ft.Column([k.muted("VYBER A HOĎ", size=12, weight=ft.FontWeight.BOLD),
                       k.text("–", size=34, weight=ft.FontWeight.BOLD, head=True),
                       k.muted("Zvol, na co házíš", size=12)], spacing=2, expand=True),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=14)
    if last.get("head"):
        big = k.text(last["head"], size=22, weight=ft.FontWeight.BOLD, head=True, color=last["color"])
    else:
        big = k.text(last["value"], size=34, weight=ft.FontWeight.BOLD, head=True, color=last["color"])
    return k.framed(ft.Row([
        shapes.die(app, last.get("die", "6"), last["value"], 96, sel=True),
        ft.Column([k.muted(last["label"].upper() if last.get("head") else last["label"], size=13,
                           weight=ft.FontWeight.BOLD if last.get("head") else None),
                   big, k.muted(last["detail"], size=12)], spacing=2, expand=True),
    ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=14, glow=True)


def _history(app) -> ft.Control:
    k = app.kit
    hist = app.char.get("history", [])[:5]
    if not hist:
        return ft.Container()
    return ft.Column([k.section("Historie", icon=ft.Icons.HOURGLASS_EMPTY),
                      k.list_card([k.row_item(h["label"], h["value"]) for h in hist])], spacing=8)


def _free_dice(app, sides_list: list[str], count: int = 1) -> ft.Control:
    """Mřížka kostek ve tvaru skutečných kostek; poslední hozená svítí."""
    k = app.kit
    l = app.look
    last = app.ui.get("dice_last") or {}
    last_die = last.get("die") if last.get("char") == app.char["id"] and last.get("free") else None

    def tile(name: str, special: bool = False) -> ft.Control:
        kind = shapes.kind_of(name)

        def roll(e):
            if name == "k6+":
                rolls = open_d6()
                _push(app, "k6+", sum(rolls), "Hody: " + " + ".join(map(str, rolls)) if len(rolls) > 1 else "Jeden hod",
                      l.hi, die="6+", free=True)
            elif name == "k%":
                _push(app, "k%", d(100), "Procentový hod (1–100)", l.hi, die="%", free=True)
            else:
                n = int(name[1:])
                rolls = [d(n) for _ in range(count)]
                _push(app, f"{count}× {name}", sum(rolls),
                      "Hody: " + " + ".join(map(str, rolls)) if count > 1 else
                      "Hozeno právě teď · klepni na kostku a hoď znovu", l.hi, die=kind, free=True)
        sel = last_die == kind and (name in ("k6+", "k%")) == (kind in ("6+", "%"))
        sub = {"k6+": "šestka se hází znovu", "k%": "procentový hod"}.get(name, f"1–{name[1:]}")
        return ft.Container(
            ft.Column([shapes.die(app, kind, None, 58, sel=sel),
                       k.text(name, size=18, weight=ft.FontWeight.BOLD, head=True, align=ft.TextAlign.CENTER,
                              color=l.orn if special else None),
                       k.muted(sub, size=11, align=ft.TextAlign.CENTER)],
                      spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=1, padding=ft.Padding.only(top=10, bottom=8, left=4, right=4),
            gradient=k.grad(l.card2, l.card), border_radius=ft.BorderRadius.all(l.radius),
            border=ft.Border.all(2, l.orn) if sel else ft.Border.all(1, l.frame if special else l.border),
            shadow=k.glow(14) if sel else None, on_click=roll, ink=True, data="die:" + name, tooltip=f"Hodit {name}")

    plain = [n for n in sides_list if n not in ("k6+", "k%")]
    special = [n for n in sides_list if n in ("k6+", "k%")]
    rows: list[ft.Control] = []
    for i in range(0, len(plain), 3):
        part = plain[i:i + 3]
        rows.append(ft.Row([tile(n) for n in part] + [ft.Container(expand=1)] * (3 - len(part)) if len(plain) > 3
                           else [tile(n) for n in part], spacing=8))
    if special:
        rows.append(ft.Row([tile(n, special=True) for n in special], spacing=8))
    return ft.Column(rows, spacing=8)


def _weapon_tab(app, exploding: bool) -> list[ft.Control]:
    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    ws = model.weapons(c)
    wi = min(app.ui.get("dice_weapon", 0), len(ws) - 1)
    rows = []
    for idx, w in enumerate(ws):
        uc = model.uc(c, w)
        rows.append(k.card(ft.Row([
            ft.Column([k.text(w["name"], size=15, weight=ft.FontWeight.W_600),
                       k.muted("střelná" if w.get("ranged") else "boj tváří v tvář")], spacing=2, expand=True),
            k.text(f"ÚČ {uc}", size=20, weight=ft.FontWeight.BOLD, head=True),
        ]), accent=idx == wi, on_click=lambda e, idx=idx: app.go("kostky", dice_weapon=idx), padding=12))
    w = ws[wi]
    uc = model.uc(c, w)

    pen, why = model.combat_penalty(c)

    def attack(e):
        rolls = open_d6() if exploding else [d(6)]
        total = uc + sum(rolls) + pen
        _push(app, f"Útok · {w['name']}", total, f"ÚČ {uc} + {'k6+' if exploding else 'k6'} ({roll_expr(rolls)})" +
              (f" {fmt(pen)} ({', '.join(why)})" if pen else ""), l.hi, die="6+" if exploding else "6")

    out = rows + [
        k.muted(f"Útok = ÚČ + {'k6+ (šestka se hází znovu)' if exploding else 'k6'}. Obránce hází OČ + "
                f"{'k6+' if exploding else 'k6'}; zasáhneš, když máš víc."),
        k.button(f"Hodit útok · {w['name']}", attack),
        k.button("Otevřít souboj se soupeřem", lambda e: app.go("souboj"), primary=False),
    ]
    if c["system"] == "dh":
        def toggle(e):
            app.settings["dh_exploding"] = e.control.value
            app.save(settings=True)
            app.refresh()
        out.insert(len(rows), ft.Switch(label="Šestka se hází znovu (k6+)", value=exploding, active_color=l.hi,
                                        on_change=toggle))
    return out


def kostky(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    is_dh = c["system"] == "dh"
    tabs = ["Dovednost", "Zbraň", "Volný hod"] if is_dh else ["Kostky", "Zbraň", "Schopnost", "Past"]
    tab = app.ui.get("dice_tab")
    if tab not in tabs:
        tab = tabs[0]

    body: list[ft.Control] = []
    if tab == "Dovednost":
        sel = app.ui.get("dice_skill")
        options = [s["name"] for s in c["skills"]]
        if sel not in options and sel not in dh.ATTRS:
            sel = options[0] if options else "OBR"
        diff = app.ui.get("dice_diff", 8)
        adv = app.ui.get("dice_adv", 0)
        rows = []
        for s in sorted(c["skills"], key=lambda s: (-s["level"], s["name"])):
            b = dh.bonus(c["attrs"][dh.ATTRS.index(s["attr"])])
            rows.append(k.card(ft.Row([
                ft.Column([k.text(s["name"], size=15, weight=ft.FontWeight.W_600),
                           k.muted(f"{s['attr']} {fmt(b)} · stupeň {s['level']}")], spacing=2, expand=True),
                k.text(fmt(b + s["level"]), size=18, weight=ft.FontWeight.BOLD, head=True),
            ]), accent=s["name"] == sel, padding=10,
                on_click=lambda e, n=s["name"]: app.go("kostky", dice_skill=n)))
        body += [k.muted("NA CO HÁZÍŠ", size=12, weight=ft.FontWeight.BOLD), *rows,
                 k.muted("…nebo jen na vlastnost bez dovednosti:", size=13),
                 k.pills(dh.ATTRS, sel if sel in dh.ATTRS else "", lambda v: app.go("kostky", dice_skill=v), equal=True),
                 k.stepper(diff, lambda e: app.go("kostky", dice_diff=max(0, diff - 1)),
                           lambda e: app.go("kostky", dice_diff=diff + 1), label="Obtížnost / nebezpečnost",
                           sub="určí PJ; výsledek ji musí překonat"),
                 k.pills(["Nevýhoda −5", "Bez úpravy", "Výhoda +5"], ["Nevýhoda −5", "Bez úpravy", "Výhoda +5"][adv + 1],
                         lambda v: app.go("kostky", dice_adv={"Nevýhoda −5": -1, "Bez úpravy": 0}.get(v, 1)), equal=True)]

        def roll_skill(e):
            if sel in dh.ATTRS:
                b, lvl, name, attr = dh.bonus(c["attrs"][dh.ATTRS.index(sel)]), 0, sel, sel
            else:
                s = next(s for s in c["skills"] if s["name"] == sel)
                b, lvl, name, attr = dh.bonus(c["attrs"][dh.ATTRS.index(s["attr"])]), s["level"], s["name"], s["attr"]
            kk, total, ok = dh.check(b, lvl, diff, adv)
            mod = f" {fmt(adv * dh.ADVANTAGE)}" if adv else ""
            _push(app, f"Ověření · {name}", total,
                  f"k10 ({kk}) {fmt(b)} {attr}" + (f" + stupeň {lvl}" if lvl else "") + mod +
                  f" – {'Úspěch' if ok else 'Neúspěch'} (obtížnost {diff})", l.ok if ok else l.bad, die="10")
        body.append(k.button(f"Hodit k10 · {sel}", roll_skill))

    elif tab == "Zbraň":
        body += _weapon_tab(app, app.settings.get("dh_exploding", True) if is_dh else True)

    elif tab == "Schopnost":
        abil = rollable_abilities(c)
        if not abil:
            body.append(k.empty("Zatím nemáš žádné schopnosti v %. Přidej je v Postava – Schopnosti."))
            body.append(k.button("Přidat schopnost", lambda e: app.go("dovednosti"), primary=False))
        else:
            sel = app.ui.get("dice_ability")
            names = [a["name"] for a in abil]
            if sel not in names:
                sel = names[0]
            pm = app.ui.get("dice_pm", 0)
            rows = [_ability_row(app, a, a["name"] == sel) for a in abil]
            body.append(ft.Column(rows, spacing=6))
            a = next(a for a in abil if a["name"] == sel)
            chance = max(1, min(99, a["chance"] + pm))
            body.append(_pm_card(app, pm, a["chance"]))

            def roll_pct(e):
                p, _ = drd.percent(chance)
                ok, txt = drd.pct_text(p, chance, c["level"])
                head, _, rest = txt.partition(" – ")
                _push(app, a["name"], p, rest or txt, l.ok if ok else l.bad, die="%", head=head)
            body.append(k.button(f"Hodit k% · {a['name']} · {chance} %", roll_pct, icon=ft.Icons.CASINO_OUTLINED,
                                 height=54))

    elif tab == "Past":
        ti = app.ui.get("dice_trap_attr", "OBR")
        danger = app.ui.get("dice_danger", 6)
        body += [k.muted("Vlastnost, proti které past působí", size=13),
                 k.pills([f"{a} {fmt(drd.bonus(c['attrs'][i]))}" for i, a in enumerate(drd.ATTRS)],
                         next((f"{a} {fmt(drd.bonus(c['attrs'][i]))}" for i, a in enumerate(drd.ATTRS) if a == ti), ""),
                         lambda v: app.go("kostky", dice_trap_attr=v.split()[0]), equal=True),
                 k.stepper(danger, lambda e: app.go("kostky", dice_danger=max(1, danger - 1)),
                           lambda e: app.go("kostky", dice_danger=danger + 1), label="Nebezpečnost pasti",
                           sub="hod musí být stejný nebo vyšší")]

        def roll_trap(e):
            b = drd.bonus(c["attrs"][drd.ATTRS.index(ti)])
            kk, total, ok = drd.trap(b, danger)
            _push(app, f"Past · {ti}", total, f"k10 ({kk}) {fmt(b)} – {'štěstí, odolal' if ok else 'smůla, past zasáhla'}"
                  f" (nebezpečnost {danger})", l.ok if ok else l.bad, die="10")
        body.append(k.button("Hodit proti pasti (k10)", roll_trap))

    else:
        r = model.rules(c["system"])
        if is_dh:
            body += [_free_dice(app, r.DICE),
                     k.muted("Dračí Hlídka: k6 pro boj, k10 pro dovednosti, kouzla a pasti. Procentový hod se nepoužívá.")]
        else:
            count = app.ui.get("dice_count", 1)
            body += [k.framed(k.stepper(f"{count}×", lambda e: app.go("kostky", dice_count=max(1, count - 1)),
                                        lambda e: app.go("kostky", dice_count=min(10, count + 1)), label="Počet kostek",
                                        sub="platí pro k4 až k20"), padding=ft.Padding.symmetric(horizontal=14, vertical=10)),
                     _free_dice(app, r.DICE, count),
                     k.muted("Dračí doupě 1.6: k6+ v boji, k10 proti pastem, k% u schopností. "
                             "Ostatní kostky pro zranění zbraní, tabulky a hody PJ.")]

    controls = [k.pills(tabs, tab, lambda v: app.go("kostky", dice_tab=v), equal=True), _result_card(app),
                *body, _history(app)]
    return Screen("Kostky", [column(controls)])


def _ability_row(app, a: dict, sel: bool) -> ft.Control:
    """Schopnost v seznamu; vybraná svítí (plný rámeček, barevné pozadí, proužek, fajfka, VYBRÁNO)."""
    k = app.kit
    l = app.look
    pick = lambda e, n=a["name"]: app.go("kostky", dice_ability=n)
    if sel:
        body = ft.Row([
            ft.Container(ft.Icon(ft.Icons.CHECK, size=16, color=l.bg), width=26, height=26, bgcolor=l.orn,
                         border_radius=ft.BorderRadius.all(13), alignment=ft.Alignment.CENTER),
            ft.Column([k.text(a["name"], size=17, weight=ft.FontWeight.BOLD, color="#ffffff"),
                       k.text(f"VYBRÁNO · {a['kind']}", size=12, weight=ft.FontWeight.BOLD, color=l.orn)],
                      spacing=1, expand=True),
            k.text(f"{a['chance']} %", size=24, weight=ft.FontWeight.BOLD, head=True, color="#ffffff"),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        return ft.Container(
            ft.Stack([ft.Container(body, padding=ft.Padding.only(left=18, right=14, top=12, bottom=12)),
                      ft.Container(width=5, bgcolor=l.orn, border_radius=ft.BorderRadius.all(3), left=0, top=6,
                                   bottom=6)]),
            border=ft.Border.all(2, l.orn), border_radius=ft.BorderRadius.all(l.radius),
            gradient=ft.LinearGradient(begin=ft.Alignment.CENTER_LEFT, end=ft.Alignment.CENTER_RIGHT,
                                       colors=[l.accent, l.card2], stops=[0.0, 0.75]),
            shadow=k.glow(18), on_click=pick, ink=True, data="ability:" + a["name"])
    return ft.Container(ft.Row([
        ft.Container(width=26, height=26, border=ft.Border.all(2, l.frame), border_radius=ft.BorderRadius.all(13)),
        ft.Column([k.text(a["name"], size=16, weight=ft.FontWeight.BOLD), k.muted(a["kind"], size=12)], spacing=1,
                  expand=True),
        k.text(f"{a['chance']} %", size=18, weight=ft.FontWeight.BOLD, head=True),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=14, vertical=11), bgcolor=l.card, border=ft.Border.all(1, l.border),
        border_radius=ft.BorderRadius.all(l.radius), opacity=0.8, on_click=pick, ink=True, data="ability:" + a["name"])


def _pm_card(app, pm: int, base: int) -> ft.Control:
    """Úprava od PJ: −/+ po 5 % a pole, do kterého jde číslo napsat (s rychlými volbami a výpočtem šance)."""
    k = app.kit
    l = app.look
    calc = ft.Text(size=14, color=l.muted)
    sub = k.muted("klepni na číslo a napiš", size=12)

    def chance_of(v: int) -> int:
        return max(1, min(99, base + v))

    def show_calc(v: int) -> None:
        sign = "−" if v < 0 else "+"
        calc.spans = [ft.TextSpan("Šance "), ft.TextSpan(f"{base} %", ft.TextStyle(weight=ft.FontWeight.BOLD, color=l.ink)),
                      ft.TextSpan(f" {sign} "),
                      ft.TextSpan(f"{abs(v)} %", ft.TextStyle(weight=ft.FontWeight.BOLD, color=l.bad if v < 0 else l.ok)),
                      ft.TextSpan(" = "),
                      ft.TextSpan(f"{chance_of(v)} %", ft.TextStyle(weight=ft.FontWeight.BOLD, size=20, color=l.warn,
                                                                     font_family=app.kit.hf))]

    def parse(text: str) -> int | None:
        t = str(text or "").replace("−", "-").replace("%", "").replace(" ", "").replace(",", ".")
        try:
            return max(-100, min(100, int(float(t or 0))))
        except ValueError:
            return None

    field = ft.TextField(value=fmt(pm), width=96, height=48, text_align=ft.TextAlign.CENTER, suffix="%",
                         keyboard_type=ft.KeyboardType.NUMBER, text_size=22, border_color=l.frame,
                         focused_border_color=l.orn, color=l.ink, cursor_color=l.orn, filled=True, fill_color=l.bg,
                         border_radius=l.radius, content_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                         text_style=ft.TextStyle(font_family=app.kit.hf,
                                                 weight=ft.FontWeight.BOLD), data="pm")

    def commit(e=None):
        v = parse(field.value)
        if v is None:
            field.value = fmt(pm)
            app.toast("Napiš číslo od −100 do +100.")
            try:
                field.update()
            except Exception:
                pass
            return
        if v != pm:
            app.go("kostky", dice_pm=v)

    def focus(e):
        extra.visible = True
        sub.value = "píšeš vlastní číslo · tlačítka −/+ dál mění po 5 %"
        try:
            extra.update()
            sub.update()
        except Exception:
            pass

    def typed(e):
        v = parse(field.value)
        if v is not None:
            show_calc(v)
            try:
                calc.update()
            except Exception:
                pass

    field.on_focus = focus
    field.on_change = typed
    field.on_submit = commit
    field.on_blur = commit
    show_calc(pm)
    chips = ft.Row([ft.Container(k.text(lbl, size=14, weight=ft.FontWeight.BOLD,
                                        color="#ffffff" if v == pm else None),
                                 padding=ft.Padding.symmetric(horizontal=10, vertical=9),
                                 bgcolor=l.accent if v == pm else l.card,
                                 border=ft.Border.all(1, l.orn if v == pm else l.border),
                                 border_radius=ft.BorderRadius.all(l.radius),
                                 on_click=lambda e, v=v: app.go("kostky", dice_pm=v), ink=True)
                    for lbl, v in (("−50", -50), ("−35", -35), ("−20", -20), ("−10", -10), ("0", 0), ("+10", 10),
                                   ("+20", 20), ("+50", 50))], spacing=6, wrap=True, run_spacing=6)
    extra = ft.Column([chips, ft.Row([calc, ft.Container(expand=True), k.muted("rozsah −100 až +100", size=12)],
                                     vertical_alignment=ft.CrossAxisAlignment.CENTER)],
                      spacing=10, visible=False)
    head = ft.Row([
        ft.Column([k.text("Úprava od PJ", size=16, weight=ft.FontWeight.BOLD), sub], spacing=2, expand=True),
        k.square_button(ft.Icons.REMOVE, lambda e: app.go("kostky", dice_pm=max(-100, pm - 5)), "Snížit o 5 %"),
        field,
        k.square_button(ft.Icons.ADD, lambda e: app.go("kostky", dice_pm=min(100, pm + 5)), "Zvýšit o 5 %"),
    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return k.framed(ft.Column([head, extra], spacing=10), padding=ft.Padding.symmetric(horizontal=14, vertical=10))


# --- souboj --------------------------------------------------------------------

def _default_foe(app) -> dict:
    sys = app.char["system"]
    best = app.bestiary.get(sys, [])
    if best:
        return foe_from_beast(best[0])
    return {"name": "Soupeř", "uc": 3, "oc": 3, "hp": 10, "hp_max": 10, "dmg": 0}


def foe_from_beast(b: dict) -> dict:
    hp = int(b.get("hp", 10) or 10)
    size = str(b.get("size", "") or "B").strip().upper()[:2]
    if size not in drd.SIZES:
        size = "B"
    return {"name": b.get("name", "Soupeř"), "uc": int(b.get("uc", 0)), "oc": int(b.get("oc", 0)), "hp": hp,
            "hp_max": hp, "dmg": int(b.get("dmg", 0)), "size": size}


RANGES = ["malý", "střední", "velký"]


def souboj(app):
    from ..core import Screen

    c = app.char
    k = app.kit
    l = app.look
    r = model.rules(c["system"])
    is_dh = c["system"] == "dh"
    exploding = app.settings.get("dh_exploding", True) if is_dh else True
    foe = app.ui.get("foe")
    if not foe or foe.get("sys") != c["system"]:
        foe = _default_foe(app)
        foe["sys"] = c["system"]
        app.ui["foe"] = foe
        app.ui["fight_log"] = []
        app.ui["round"] = 1
    log = app.ui.setdefault("fight_log", [])
    ws = model.weapons(c)
    wi = min(app.ui.get("dice_weapon", 0), len(ws) - 1)
    w = ws[wi]
    uc = model.uc(c, w)
    my_oc = model.oc(c, w)
    pen, why = model.combat_penalty(c)
    my_size = model.size(c)
    foe_size = foe.get("size", "B")
    dist = app.ui.get("fight_range", "střední")
    if is_dh:
        att_mod, foe_mod, mod_txt = pen, 0, ", ".join(why)
    elif w.get("ranged"):
        rmod = {"malý": 1, "střední": 0, "velký": -1}[dist]
        att_mod = pen + rmod + drd.ranged_size_mod(foe_size)
        foe_mod = 0
        mod_txt = ", ".join(why + [f"dostřel {dist} {fmt(rmod)}"] +
                            ([f"cíl {foe_size} +1"] if drd.ranged_size_mod(foe_size) else []))
    else:
        smod = drd.size_mod(my_size, foe_size)
        att_mod = pen + smod
        foe_mod = drd.size_mod(foe_size, my_size)
        mod_txt = ", ".join(why + ([f"velikost {my_size} proti {foe_size} {fmt(smod)}"] if smod else []))
    def_mod = pen  # postih za zranění, naložení či únavu platí i pro obranu

    def roll():
        return open_d6() if exploding else [d(6)]

    def note(text, color):
        log.insert(0, {"t": text, "c": color})
        del log[8:]

    def my_attack(e):
        a, dd = roll(), roll()
        at, de = uc + sum(a) + att_mod, foe["oc"] + sum(dd)
        wound = r.wound(at, de, int(w.get("damage", 0)))
        mtxt = f" {fmt(att_mod)}" if att_mod else ""
        if wound:
            foe["hp"] = foe["hp"] - wound
            note(f"Útok {at} ({uc}+{roll_expr(a)}{mtxt}) proti obraně {de} ({foe['oc']}+{roll_expr(dd)}) – zásah za {wound}",
                 l.hi)
            if foe["hp"] <= 0:
                note(f"{foe['name']} padl!", l.ok)
        else:
            note(f"Útok {at} proti obraně {de} – vedle", l.mana)
        app.ui["round"] += 1
        app.refresh()

    def foe_attack(e):
        a, dd = roll(), roll()
        at, de = foe["uc"] + sum(a) + foe_mod, my_oc + sum(dd) + def_mod
        wound = r.wound(at, de, foe["dmg"])
        if wound:
            c["hp"] -= wound
            model.add_history(c, f"Zranění od: {foe['name']}", f"−{wound}")
            app.save(c)
            note(f"{foe['name']}: útok {at} proti tvé obraně {de} – zranění {wound}", l.bad)
            st = model.status(c)
            if st:
                note(f"Ty: {st[0]}", l.bad)
        else:
            note(f"{foe['name']}: útok {at} proti tvé obraně {de} – ubránil ses", l.ok)
        app.refresh()

    def initiative(e):
        if is_dh:
            kk, mine = dh.initiative(dh.bonus(c["attrs"][1]))
            theirs = d(6)
            note(f"Iniciativa: ty {mine} (k6 {kk} {fmt(dh.bonus(c['attrs'][1]))} OBR), soupeř {theirs}", l.ink)
        else:
            mine, theirs = d(6), d(6)
            note(f"Iniciativa: ty {mine}, soupeř {theirs}" + (" – začínáš" if mine > theirs else
                                                              " – začíná soupeř" if theirs > mine else " – znovu"), l.ink)
        app.refresh()

    def edit_foe(e):
        names = ["(vlastní)"] + [b["name"] for b in app.bestiary.get(c["system"], [])]

        def save(v):
            if v["pick"] and v["pick"] != "(vlastní)":
                b = next(b for b in app.bestiary[c["system"]] if b["name"] == v["pick"])
                nf = foe_from_beast(b)
            else:
                nf = {"name": v["name"] or "Soupeř", "uc": v["uc"], "oc": v["oc"], "hp": v["hp"], "hp_max": v["hp"],
                      "dmg": v["dmg"], "size": v.get("size") or "B"}
            nf["sys"] = c["system"]
            app.ui["foe"] = nf
            app.ui["fight_log"] = []
            app.ui["round"] = 1
            app.refresh()
        app.form("Soupeř", [("pick", "Z bestiáře", "(vlastní)", "choice", names),
                            ("name", "Jméno", foe["name"], "text"), ("uc", "ÚČ", foe["uc"], "int"),
                            ("oc", "OČ", foe["oc"], "int"), ("hp", "Životy", foe["hp_max"], "int"),
                            ("dmg", "Zranění zbraně / útočnost", foe["dmg"], "int")] +
                 ([] if is_dh else [("size", "Velikost (A0, A, B, C, D, E)", foe.get("size", "B"), "choice", drd.SIZES)]),
                 save, save_label="Nastavit")

    me_card = k.card(ft.Column([
        k.muted("TY", size=11, weight=ft.FontWeight.BOLD),
        k.text(c["name"].split()[0], size=16, weight=ft.FontWeight.BOLD, max_lines=1),
        k.muted(w["name"], max_lines=1),
        k.text(f"ÚČ {uc} · {'OČ' if is_dh else 'obr.'} {my_oc}", size=17, weight=ft.FontWeight.BOLD, head=True,
               color=l.hi),
        k.muted(f"velikost {my_size}" + (f" · postih {pen}" if pen else ""), size=12),
        k.bar(c["hp"], c["hp_max"], l.hp), k.muted(f"Životy {c['hp']} / {c['hp_max']}"),
    ], spacing=3), padding=12)
    foe_card = k.card(ft.Column([
        k.muted("SOUPEŘ", size=11, weight=ft.FontWeight.BOLD),
        k.text(foe["name"], size=16, weight=ft.FontWeight.BOLD, max_lines=1),
        k.muted(f"zranění {fmt(foe['dmg'])}" + ("" if is_dh else f" · velikost {foe_size}")),
        k.text(f"ÚČ {foe['uc']} · OČ {foe['oc']}", size=17, weight=ft.FontWeight.BOLD, head=True, color=l.mana),
        k.bar(max(0, foe["hp"]), foe["hp_max"], l.hp), k.muted(f"Životy {foe['hp']} / {foe['hp_max']}"),
    ], spacing=3), padding=12, on_click=edit_foe)

    weapon_pills = k.pills([x["name"] for x in ws], w["name"],
                           lambda v: app.go("souboj", dice_weapon=[x["name"] for x in ws].index(v)))
    log_rows = [k.text(x["t"], size=13, color=x["c"]) for x in log] or [k.muted("Zatím žádné hody.")]
    controls = [
        ft.Row([ft.Container(me_card, expand=1), ft.Container(foe_card, expand=1)], spacing=8,
               vertical_alignment=ft.CrossAxisAlignment.START),
        k.muted("Klepnutím na soupeře ho změníš nebo vybereš z bestiáře.", size=12),
        weapon_pills,
        *([k.pills(RANGES, dist, lambda v: app.go("souboj", fight_range=v), equal=True)]
          if (w.get("ranged") and not is_dh) else []),
        *([k.muted(f"Opravy útoku: {mod_txt} = {fmt(att_mod)}", size=12)] if (att_mod or mod_txt) else []),
        ft.Row([k.button("Útočím", my_attack, expand=1), k.button("Soupeř útočí", foe_attack, primary=False, expand=1)],
               spacing=8),
        ft.Row([k.button("Iniciativa", initiative, primary=False, expand=1),
                k.button("Nový boj", lambda e: (app.ui.update({"foe": None}), app.refresh()), primary=False, expand=1)],
               spacing=8),
        k.section(f"Průběh · kolo {app.ui.get('round', 1)}"),
        k.card(ft.Column(log_rows, spacing=6)),
        k.muted(("Útok ÚČ + k6, obrana OČ + k6" + (" (šestka se hází znovu)" if exploding else "") +
                 ". Zranění = rozdíl + zranění zbraně.") if is_dh else
                "Útok ÚČ + k6+, obrana OČ + k6+. Zranění = rozdíl + útočnost zbraně (nejméně 1)."),
    ]
    return Screen("Souboj", [column(controls)])
