"""Společné pomůcky pro obrazovky propojení: točící se kolečko, chyby spojení, čas „před 3 min“."""
from __future__ import annotations

import time

import flet as ft

from .. import stul, sync


def ago(ts) -> str:
    ts = sync._parse_ts(ts)
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


def busy(app, text: str) -> ft.AlertDialog:
    k = app.kit
    dlg = ft.AlertDialog(
        modal=True, content=ft.Row([ft.ProgressRing(width=22, height=22, color=app.look.hi),
                                    k.text(text, size=15)], spacing=14, tight=True))
    app.page.show_dialog(dlg)
    return dlg


def info(app, title: str, text: str, big: str | None = None, extra: list[ft.Control] | None = None) -> None:
    k = app.kit
    body: list[ft.Control] = []
    if big:
        body.append(ft.Container(k.text(big, size=40, weight=ft.FontWeight.BOLD, head=True, color=app.look.hi,
                                        align=ft.TextAlign.CENTER), alignment=ft.Alignment.CENTER,
                                 padding=ft.Padding.symmetric(vertical=10)))
    body.append(k.muted(text, size=14))
    body += extra or []
    app.page.show_dialog(ft.AlertDialog(
        title=k.text(title, size=19, weight=ft.FontWeight.BOLD, head=True), bgcolor=app.look.card,
        content=ft.Container(ft.Column(body, spacing=8, tight=True, scroll=ft.ScrollMode.AUTO), width=340),
        actions=[ft.TextButton("Rozumím", on_click=lambda e: app.close_dialog())]))


def remote(app, title: str, coro_factory, ok_msg=None, after=None) -> None:
    """Spustí operaci se serverem nebo stolem s kolečkem a srozumitelnou chybou."""
    async def run():
        dlg = busy(app, title)
        try:
            result = await coro_factory()
        except ValueError as ex:
            app.close_dialog(dlg)
            app.toast(str(ex))
            return
        except stul.TableError as ex:
            app.close_dialog(dlg)
            info(app, "U stolu", str(ex))
            return
        except sync.SyncError as ex:
            app.close_dialog(dlg)
            info(app, "Nepovedlo se", str(ex))
            return
        except OSError:
            app.close_dialog(dlg)
            info(app, "Bez připojení", "Server ani stůl PJ není dostupný. Zkontroluj připojení a zkus to znovu.")
            return
        except Exception as ex:  # nic nesmí nechat kolečko točit se
            app.close_dialog(dlg)
            info(app, "Nepovedlo se", f"Neočekávaná chyba: {ex}")
            return
        app.close_dialog(dlg)
        if after:
            r = after(result)
            if hasattr(r, "__await__"):
                await r
        app.start_sync_loop()
        app.refresh()
        if ok_msg:
            app.toast(ok_msg() if callable(ok_msg) else ok_msg)
    app.run(run())


def initials(name: str) -> str:
    parts = [p for p in str(name or "?").replace("–", " ").split() if p[:1].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def member_sub(snap: dict, level_word: str = "úroveň") -> str:
    return " · ".join(str(x) for x in (snap.get("race"), snap.get("cls"),
                                       f"{snap.get('level')}. {level_word}" if snap.get("level") else None) if x)
