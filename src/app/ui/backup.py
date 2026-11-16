"""Záloha a obnova všech dat (postavy, bestiář, nastavení, obrázky) do jednoho souboru JSON."""
from __future__ import annotations

import base64
import json
import time

import flet as ft

from .. import model

FORMAT = 1
REMIND_DAYS = 14


def image_refs(c: dict) -> list[str]:
    refs = [img["ref"] for img in c.get("images", []) if img.get("ref")]
    if c.get("avatar"):
        refs.append(c["avatar"])
    return refs


async def build_backup(app) -> bytes:
    images: dict[str, str] = {}
    for cid in app.order:
        for ref in image_refs(app.chars[cid]):
            data = app.images.get(ref) or await app.store.load_image(ref)
            if data:
                images[ref] = base64.b64encode(data).decode("ascii")
    payload = {
        "app": "denik-dobrodruha", "format": FORMAT, "exported": time.strftime("%Y-%m-%d %H:%M"),
        "order": list(app.order), "chars": [app.chars[cid] for cid in app.order],
        "bestiary": app.bestiary, "settings": {k: v for k, v in app.settings.items() if k != "last_backup"},
        "images": images,
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def parse_backup(raw: bytes) -> dict:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict) or data.get("app") != "denik-dobrodruha" or not isinstance(data.get("chars"), list):
        raise ValueError("Tohle není záloha Deníku dobrodruha.")
    if int(data.get("format", 0)) > FORMAT:
        raise ValueError("Záloha je z novější verze aplikace – nejdřív aplikaci aktualizuj.")
    return data


async def restore(app, data: dict) -> int:
    """Sloučí zálohu s daty v zařízení: postavy se stejným id nahradí, ostatní přidá. Vrací počet postav."""
    remap: dict[str, str] = {}
    for old_ref, b64 in (data.get("images") or {}).items():
        try:
            raw = base64.b64decode(b64)
        except (ValueError, TypeError):
            continue
        new_ref = await app.store.save_image(model.new_id(), raw)
        app.images[new_ref] = raw
        remap[old_ref] = new_ref
    count = 0
    for c in data["chars"]:
        if not isinstance(c, dict) or "id" not in c or "system" not in c:
            continue
        for img in c.get("images", []):
            if img.get("ref") in remap:
                img["ref"] = remap[img["ref"]]
        if c.get("avatar") in remap:
            c["avatar"] = remap[c["avatar"]]
        app.chars[c["id"]] = c
        if c["id"] not in app.order:
            app.order.append(c["id"])
        await app.store.set_json("char." + c["id"], c)
        count += 1
    await app.store.set_json("order", app.order)
    for sys_key, beasts in (data.get("bestiary") or {}).items():
        if sys_key in app.bestiary and isinstance(beasts, list):
            known = {b.get("id") for b in app.bestiary[sys_key]}
            app.bestiary[sys_key] += [b for b in beasts if b.get("id") not in known]
            await app.store.set_json("bestiary." + sys_key, app.bestiary[sys_key])
    for key, val in (data.get("settings") or {}).items():
        if key == "custom_items" and isinstance(val, dict):
            mine = app.settings.setdefault("custom_items", {})
            for sys_key, lst in val.items():
                names = {t.get("name") for t in mine.get(sys_key, [])}
                mine.setdefault(sys_key, []).extend(t for t in lst if t.get("name") not in names)
        elif key not in app.settings:
            app.settings[key] = val
    await app.store.set_json("settings", app.settings)
    return count


def export_backup(app) -> None:
    async def run():
        raw = await build_backup(app)
        name = f"denik-zaloha-{time.strftime('%Y-%m-%d')}.json"
        try:
            await app.picker.save_file(dialog_title="Uložit zálohu", file_name=name, src_bytes=raw,
                                       file_type=ft.FilePickerFileType.CUSTOM, allowed_extensions=["json"])
        except Exception as ex:  # pragma: no cover - závisí na platformě
            app.toast(f"Zálohu se nepodařilo uložit: {ex}")
            return
        app.settings["last_backup"] = time.time()
        app.save(settings=True)
        app.toast(f"Záloha {name} je připravená ({len(raw) // 1024} kB).")
        app.refresh()
    app.run(run())


def import_backup(app) -> None:
    async def run():
        files = await app.picker.pick_files(dialog_title="Vyber zálohu", file_type=ft.FilePickerFileType.CUSTOM,
                                            allowed_extensions=["json"], with_data=True)
        if not files:
            return
        f = files[0]
        raw = getattr(f, "bytes", None)
        if not raw and getattr(f, "path", None):
            with open(f.path, "rb") as fh:
                raw = fh.read()
        try:
            data = parse_backup(raw or b"")
        except (ValueError, UnicodeDecodeError) as ex:
            app.toast(str(ex) if isinstance(ex, ValueError) and "Deník" in str(ex) else "Soubor nejde načíst.")
            return
        n = len(data["chars"])

        def go():
            async def do():
                count = await restore(app, data)
                app.toast(f"Obnoveno {count} postav ze zálohy {data.get('exported', '')}.")
                app.refresh()
            app.run(do())
        app.confirm("Obnovit ze zálohy?",
                    f"Záloha z {data.get('exported', '?')} obsahuje {n} postav. Postavy se stejným id se přepíšou "
                    "verzí ze zálohy, ostatní zůstanou.", go, yes_label="Obnovit")
    app.run(run())


def backup_card(app) -> ft.Control:
    k = app.kit
    l = app.look
    last = app.settings.get("last_backup")
    if last:
        days = int((time.time() - float(last)) // 86400)
        when = "dnes" if days == 0 else f"před {days} dny" if days > 1 else "včera"
        info = f"Poslední záloha {when}."
    else:
        info = "Zatím žádná záloha."
    warn = bool(app.order) and (not last or time.time() - float(last) > REMIND_DAYS * 86400)
    return k.card(ft.Column([
        ft.Row([ft.Icon(ft.Icons.WARNING_AMBER if warn else ft.Icons.SAVE_OUTLINED,
                        color=l.warn if warn else l.hi),
                k.text("Záloha dat", size=15, weight=ft.FontWeight.W_600, expand=True)]),
        k.muted(info + " Data jsou jen v tomto zařízení – prohlížeč je může smazat. Zálohu si ulož do souboru a "
                "kdykoli ji obnov (i na jiném zařízení).", size=13),
        ft.Row([k.button("Zálohovat", lambda e: export_backup(app), icon=ft.Icons.DOWNLOAD, expand=True),
                k.button("Obnovit", lambda e: import_backup(app), primary=False, icon=ft.Icons.UPLOAD, expand=True)],
               spacing=8),
    ], spacing=8), accent=warn)
