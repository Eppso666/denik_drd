"""Okno výsledku seslání kouzla (a výroby alchymisty) podle návrhu z 25. 11. 2026:
verdikt k% (padlo vs. potřeba), hod na zranění / léčení / zásah podle pravidel, past pro terč a útrata magů."""
from __future__ import annotations

import flet as ft

from .. import model
from ..rules import drd_ucinky
from ..rules.common import d
from . import dice_shapes as shapes


def _verdict(app, title: str, ok: bool, roll: int | None, chance: int | None, word: str, sub: str | None = None):
    k = app.kit
    l = app.look
    col = l.ok if ok else l.bad
    if roll is None:
        line = sub or "sesláno"
        pic = ft.Icon(ft.Icons.AUTO_AWESOME, size=40, color=col)
    else:
        line = (f"padlo {roll} ≤ {chance} %" if ok else f"padlo {roll}, potřeba nejvýš {chance}") + (
            f" · {sub}" if sub else "")
        pic = shapes.die(app, "%", str(roll), 64)
    return ft.Container(ft.Row([
        pic,
        ft.Column([k.text(word.upper(), size=12, weight=ft.FontWeight.BOLD, color=col),
                   k.text(title, size=20, weight=ft.FontWeight.BOLD, head=True, max_lines=2),
                   k.muted(line, size=13)], spacing=2, expand=True),
    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=14,
        border=ft.Border.all(1, col), border_radius=ft.BorderRadius.all(l.radius), bgcolor=l.card2, data="verdict")


def _mana_line(app, c: dict, spent: int, extra: str = "") -> ft.Control:
    l = app.look
    return ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, size=15, color=l.mana),
                   app.kit.muted(f"−{spent} magů · zbývá {int(c.get('mana', 0))}{extra}", size=13)], spacing=8)


def _effect_box(app, c: dict, name: str, spent: int) -> ft.Control | None:
    """Oddíl s hodem na zranění / léčení podle pravidel (stav drží sám v sobě)."""
    e = drd_ucinky.effect(name)
    if not e:
        return None
    k = app.kit
    l = app.look
    n_dice, sides, add = e["dice"]
    times = drd_ucinky.count(name, spent)
    forms = {"blesk": ("blesk", "blesky", "blesků"), "kus": ("kus", "kusy", "kusů")}.get(e.get("per"))
    unit = (forms[0] if times == 1 else forms[1] if 1 < times < 5 else forms[2]) if forms else None
    title = ft.Text(size=15, weight=ft.FontWeight.BOLD, font_family=k.hf, color=l.ink)
    area = ft.TextField(label="Čtverečních sáhů terče", value="1", keyboard_type=ft.KeyboardType.NUMBER,
                        width=200, border_color=l.frame, focused_border_color=l.hi, color=l.ink) \
        if e.get("per") == "sáh" else None
    out = ft.Column(spacing=8)
    total_txt = k.text("", size=30, weight=ft.FontWeight.BOLD, head=True, color=l.hi)

    def head_text() -> str:
        cnt = times if unit else (max(1, int(area.value or 1)) if area else 1)
        what = f"{e['kind'].capitalize()} · " + (f"{cnt} {unit} × " if unit else (f"{cnt} sáh × " if area else ""))
        return what + drd_ucinky.dice_label(e["dice"])

    def roll(ev=None):
        cnt = times if unit else (max(1, int(area.value or 1)) if area else 1)
        hit = None
        if e.get("hit"):
            hr = d(100)
            hit = (hr, hr <= e["hit"])
        rows: list[ft.Control] = []
        total = 0
        if hit is not None:
            rows.append(k.text(f"zásah {hit[0]} {'≤' if hit[1] else '>'} {e['hit']} % · "
                               f"{'zasáhly všechny blesky' if hit[1] else 'blesky minuly'}", size=13,
                               color=l.ok if hit[1] else l.bad))
        chips: list[ft.Control] = []
        for _ in range(cnt):
            vals = [d(sides) for _ in range(n_dice)]
            val = sum(vals) + add
            if hit is None or hit[1]:
                total += val
            if len(chips) < 12:
                chips += [shapes.die(app, str(sides), str(v), 40, sel=hit is None or hit[1]) for v in vals]
        if cnt * n_dice > 12:
            chips.append(k.muted(f"… celkem {cnt * n_dice} kostek", size=12))
        if add:
            chips.append(k.text(f"+{add}" + (f" ×{cnt}" if cnt > 1 else ""), size=16, weight=ft.FontWeight.BOLD,
                                head=True))
        rows.append(ft.Row([ft.Row(chips, spacing=6, wrap=True, expand=True), total_txt],
                           vertical_alignment=ft.CrossAxisAlignment.CENTER))
        total_txt.value = str(total)
        model.add_history(c, f"{e['kind'].capitalize()} · {name}", str(total))
        app.save(c)
        out.controls = [title, *rows, *([k.muted(e["note"], size=12)] if e.get("note") else [])]
        try:
            out.update()
        except Exception:  # pragma: no cover - mimo stránku (testy)
            pass

    title.value = head_text()
    if area is not None:
        def changed(ev):
            title.value = head_text()
            try:
                title.update()
            except Exception:  # pragma: no cover
                pass
        area.on_change = changed
    btn = k.button(f"Hodit {head_text().split(' · ', 1)[1]}", roll, icon=ft.Icons.CASINO_OUTLINED, height=46)
    btn.data = "roll-effect"
    out.controls = [title, *([area] if area else []), btn,
                    *([k.muted(e["note"], size=12)] if e.get("note") else [])]
    return k.framed(out, padding=12)


def show(app, c: dict, name: str, spent: int, ok: bool, roll: int | None = None, chance: int | None = None,
         word: str | None = None, trap: str | None = None, duration: str | None = None,
         note: str | None = None) -> None:
    """Otevře okno výsledku. roll=None = bez hodu na úspěch (hraničář)."""
    k = app.kit
    l = app.look
    word = word or ("Úspěch" if ok else "Neúspěch")
    body: list[ft.Control] = [_verdict(app, name, ok, roll, chance, word)]
    if ok:
        box = _effect_box(app, c, name, spent)
        if box is not None:
            body.append(box)
        if trap:
            body.append(k.parch(ft.Column([
                k.text("Past pro terč", size=14, weight=ft.FontWeight.BOLD, head=True, color=l.ptext),
                k.text(trap, size=22, weight=ft.FontWeight.BOLD, head=True, color=l.ptext),
                k.text("Na past hází Pán jeskyně za terč. Když terč neodolá, kouzlo působí"
                       + (f"; trvání {duration} se odpočítává v Aktivních účincích." if duration else "."),
                       size=13, color=l.pmuted),
            ], spacing=4)))
        if note:
            body.append(k.muted(note, size=13))
    else:
        body.append(k.muted(note or "Kouzlo se nepovedlo. Magenergie se spotřebuje i tak, trvání se nespustí.",
                            size=13))
    body.append(_mana_line(app, c, spent))

    def done(e):
        app.close_dialog(dlg)
        app.refresh()  # překreslí se až po dozavření okna (App.render)

    dlg = ft.AlertDialog(
        bgcolor=l.card, content=ft.Container(ft.Column(body, spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
                                             width=360),
        actions=[ft.FilledButton(content=ft.Text("Hotovo" if ok else "Zavřít"), on_click=done,
                                 style=ft.ButtonStyle(bgcolor=l.accent, color=l.on_accent))],
        scrollable=True, data="spell-result")
    app.open_dialog(dlg)
