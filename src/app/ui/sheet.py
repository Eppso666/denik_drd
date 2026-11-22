"""Tabulka zkušeností a tisk listu postavy (HTML soubor, který se z prohlížeče vytiskne nebo uloží do PDF)."""
from __future__ import annotations

import html
import time

import flet as ft

from .. import model
from ..rules import dh, drd
from ..rules.common import fmt


# --- tabulka zkušeností -----------------------------------------------------------------------

def xp_rows(c: dict) -> list[tuple[int, int, int | None]]:
    """(úroveň, potřebné zkušenosti, cena výcviku v zl / None)."""
    out = []
    if c["system"] == "dh":
        for lv in range(1, dh.MAX_LEVEL + 1):
            out.append((lv, dh.xp_for_level(lv), None))
    else:
        for lv in range(1, drd.MAX_XP_LEVEL + 1):
            xp = drd.xp_for_level(c["cls"], lv)
            if xp is None:
                break
            out.append((lv, xp, drd.training_cost(c["cls"], lv)))
    return out


def xp_table_dialog(app, c: dict) -> None:
    k = app.kit
    l = app.look
    rows: list[ft.Control] = []
    for lv, xp, cost in xp_rows(c):
        cur = lv == c["level"]
        color = l.hi if cur else (l.muted if lv < c["level"] else None)
        cells = [k.text(f"{lv}.", size=13, weight=ft.FontWeight.BOLD if cur else None, color=color, expand=1),
                 k.text(f"{xp:,}".replace(",", " "), size=13, color=color, expand=2, align=ft.TextAlign.RIGHT)]
        if cost is not None:
            cells.append(k.text(f"{cost} zl", size=13, color=color, expand=2, align=ft.TextAlign.RIGHT))
        rows.append(ft.Row(cells, spacing=8))
    head = [k.muted("úroveň", size=12, expand=1), k.muted("zkušenosti", size=12, expand=2, align=ft.TextAlign.RIGHT)]
    if c["system"] == "drd":
        head.append(k.muted("výcvik", size=12, expand=2, align=ft.TextAlign.RIGHT))
    nxt = model.xp_next(c)
    note = (f"Máš {c['xp']} zkušeností" + (f", na další úroveň chybí {max(0, nxt - c['xp'])}." if nxt else "."))
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(f"Zkušenosti – {c['cls']}", size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=l.card,
        content=ft.Container(ft.Column([k.muted(note, size=13), ft.Row(head, spacing=8), *rows],
                                       spacing=4, tight=True, scroll=ft.ScrollMode.AUTO), width=340, height=460),
        actions=[ft.TextButton("Zavřít", on_click=lambda e: app.close_dialog())]))


# --- tisk listu postavy ----------------------------------------------------------------------

_CSS = """
body{font-family:Georgia,'DejaVu Serif',serif;color:#222;max-width:760px;margin:24px auto;padding:0 16px}
h1{margin:0;font-size:28px} h2{font-size:17px;border-bottom:2px solid #7a1f1f;color:#7a1f1f;margin:18px 0 6px}
.sub{color:#555;margin:2px 0 10px} table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top} th{background:#f1ece2}
.grid{display:flex;gap:10px;flex-wrap:wrap} .box{border:1px solid #bbb;padding:6px 10px;min-width:70px;text-align:center}
.box b{display:block;font-size:20px} .muted{color:#666;font-size:12px}
@media print{body{margin:0} button{display:none}}
"""


def _e(v) -> str:
    return html.escape(str(v))


def _table(head: list[str], rows: list[list]) -> str:
    if not rows:
        return "<p class='muted'>–</p>"
    h = "".join(f"<th>{_e(x)}</th>" for x in head)
    b = "".join("<tr>" + "".join(f"<td>{_e(x)}</td>" for x in r) + "</tr>" for r in rows)
    return f"<table><tr>{h}</tr>{b}</table>"


def sheet_html(c: dict) -> str:
    """Celý list postavy jako samostatná HTML stránka."""
    from . import magic  # kvůli kouzlům hraničáře / kouzelníka
    from ..rules import drd_hranicar

    is_dh = c["system"] == "dh"
    r = model.rules(c["system"])
    bonus = dh.bonus if is_dh else drd.bonus
    p: list[str] = [f"<!DOCTYPE html><html lang='cs'><head><meta charset='utf-8'><title>{_e(c['name'])}</title>"
                    f"<style>{_CSS}</style></head><body>"]
    p.append(f"<h1>{_e(c['name'])}</h1><p class='sub'>{_e(r.NAME)} · {_e(c['race'])} · "
             f"{_e(magic.branch_label(c))} · {c['level']}. úroveň · zkušenosti {c['xp']}"
             + (f" / {model.xp_next(c)}" if model.xp_next(c) else "")
             + (f" · přesvědčení {_e(drd.alignment(c['alignment'])[1])}"
                if c["system"] == "drd" and drd.alignment(c.get("alignment")) else "") + "</p>")
    boxes = [("Životy", f"{c['hp']}/{c['hp_max']}")]
    if c.get("mana_max"):
        boxes.append((c.get("mana_name") or "Mana", f"{c.get('mana', 0)}/{c['mana_max']}"))
    boxes += [(a, f"{v} ({fmt(bonus(v))})") for a, v in zip(r.ATTRS, c["attrs"])]
    p.append("<div class='grid'>" + "".join(f"<div class='box'>{_e(a)}<b>{_e(v)}</b></div>" for a, v in boxes)
             + "</div>")
    ratio = model.load_ratio(c)
    if is_dh:
        p.append(f"<p class='muted'>Velikost {model.size(c)} · pohyblivost "
                 f"{dh.movement(c['race'], c['attrs'], ratio)} · hranice smrti {c.get('death', '')}</p>")
    else:
        obj, mech = drd.perception(c["race"], c["attrs"])
        p.append(f"<p class='muted'>Velikost {model.size(c)} · pohyblivost {drd.movement(c['race'], c['attrs'], ratio)}"
                 f" · postřeh objekty {obj} %, mechanismy {mech} % · mez vyřazení "
                 f"{drd.knockout_limit(c['hp_max'], c['attrs'][2])}</p>")

    p.append("<h2>Boj</h2>")
    rows = []
    for w in model.weapons(c):
        stats = (f"útočnost {w.get('attack', 0)}, zranění {fmt(int(w.get('damage', 0)))}, obrana {w.get('defense', 0)}"
                 if is_dh else f"SZ {w.get('attack', 0)}, útočnost {fmt(int(w.get('damage', 0)))}, "
                               f"OZ {fmt(int(w.get('defense', 0)))}")
        rows.append([w["name"], stats, model.uc(c, w), model.oc(c, w)])
    p.append(_table(["Zbraň", "Parametry", "ÚČ", "OČ" if is_dh else "Obrana"], rows))
    p.append(f"<p class='muted'>Zbroj {model.armor_quality(c)} · štít {fmt(model.shield_bonus(c))}</p>")

    if is_dh:
        p.append("<h2>Dovednosti</h2>")
        p.append(_table(["Dovednost", "Atribut", "Stupeň"],
                        [[s["name"], s["attr"], s["level"]] for s in sorted(c["skills"], key=lambda s: s["name"])]))
    else:
        p.append("<h2>Schopnosti</h2>")
        rows = [[a["name"], f"{a['pct']} %" if a.get("pct") is not None else a.get("sub", "")]
                for a in drd.class_abilities(c["cls"], c["level"], c["attrs"], c.get("branch")) if not a["locked"]]
        rows += [[a["name"], f"{a.get('pct', '')} %"] for a in c.get("abilities", [])]
        p.append(_table(["Schopnost", "Hodnota"], rows))

    spells = []
    if magic.is_wizard(c):
        spells = [magic.find_spell(n) for n in c.get("spells", [])]
    elif magic.is_ranger(c):
        spells = drd_hranicar.ranger_spells(c["level"], c.get("branch"))
    spells = [s for s in spells if s]
    if spells:
        p.append("<h2>Kouzla</h2>")
        p.append(_table(["Kouzlo", "Magenergie", "Dosah", "Vyvolání", "Trvání"],
                        [[s["name"], s["mana"], s["reach"], s["cast"], s["duration"]] for s in spells]))
    if c.get("abilities_mind"):
        p.append("<h2>Mimosmyslové schopnosti</h2>")
        p.append(_table(["Schopnost", "Stupeň", "Hodnota"],
                        [[h["name"], drd_hranicar.ability_grade(c["level"], h["since"]),
                          drd_hranicar.ability_value(h["name"], drd_hranicar.ability_grade(c["level"], h["since"]))]
                         for h in c["abilities_mind"]]))
    if c.get("companions"):
        p.append("<h2>Společníci</h2>")
        p.append(_table(["Jméno", "Druh"], [[x.get("nick") or x.get("name", ""), f"{x.get('kind', '')}: {x.get('name', '')}"]
                                            for x in c["companions"]]))

    p.append("<h2>Výbava</h2>")
    m = c.get("money", {})
    p.append(f"<p>Peníze: {m.get('zl', 0)} zl {m.get('st', 0)} st {m.get('md', 0)} md</p>")
    p.append(_table(["Předmět", "Druh", "Ks", "Na těle"],
                    [[i["name"], i["category"], i.get("qty", 1), "ano" if i.get("equipped") else ""]
                     for i in c.get("items", [])]))
    notes = [n for n in c.get("notes", []) if isinstance(n, dict) and n.get("pinned")]
    if notes:
        p.append("<h2>Připnuté poznámky</h2>")
        for n in notes:
            p.append(f"<p><b>{_e(n.get('title', ''))}</b><br>" + _e(n.get("text", "")).replace("\n", "<br>") + "</p>")
    p.append(f"<p class='muted'>Vytištěno z Deníku dobrodruha {time.strftime('%d. %m. %Y')}.</p>"
             "<button onclick='window.print()'>Tisk / uložit jako PDF</button></body></html>")
    return "".join(p)


def export_sheet(app, c: dict) -> None:
    async def run():
        data = sheet_html(c).encode("utf-8")
        name = "".join(ch for ch in c["name"] if ch.isalnum() or ch in " -_").strip() or "postava"
        try:
            await app.picker.save_file(dialog_title="Uložit list postavy", file_name=f"{name}.html", src_bytes=data,
                                       file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["html"])
        except Exception as ex:  # pragma: no cover - závisí na platformě
            app.toast(f"List se nepodařilo uložit: {ex}")
            return
        app.toast("List postavy uložen – otevři ho v prohlížeči a dej Tisk (nebo Uložit jako PDF).")
    app.run(run())
