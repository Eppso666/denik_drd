"""Ukládání dat v zařízení.

Postavy a bestiář se ukládají jako JSON do SharedPreferences (Android, iOS i prohlížeč).
Obrázky: v mobilní aplikaci jako soubory ve složce aplikace, ve webové verzi jako base64
v úložišti prohlížeče (prohlížeče mají limit zhruba 5 MB, proto se obrázky zmenšují).
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import flet as ft

PREFIX = "denik.v1."


class Storage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.prefs = ft.SharedPreferences()
        data_dir = os.getenv("FLET_APP_STORAGE_DATA")
        self.files_dir = None
        if data_dir and not getattr(page, "web", False):
            self.files_dir = os.path.join(data_dir, "images")
            os.makedirs(self.files_dir, exist_ok=True)

    async def get_json(self, key: str, default: Any) -> Any:
        try:
            raw = await self.prefs.get(PREFIX + key)
        except Exception:
            return default
        if not raw:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    async def set_json(self, key: str, value: Any) -> None:
        await self.prefs.set(PREFIX + key, json.dumps(value, ensure_ascii=False))

    async def remove(self, key: str) -> None:
        try:
            await self.prefs.remove(PREFIX + key)
        except Exception:
            pass

    # --- obrázky -------------------------------------------------------------
    async def save_image(self, image_id: str, data: bytes) -> str:
        """Uloží obrázek a vrátí odkaz pro načtení ('file:' nebo 'pref:')."""
        if self.files_dir:
            path = os.path.join(self.files_dir, f"{image_id}.img")
            with open(path, "wb") as f:
                f.write(data)
            return "file:" + path
        await self.prefs.set(PREFIX + "img." + image_id, base64.b64encode(data).decode("ascii"))
        return "pref:" + image_id

    async def load_image(self, ref: str) -> bytes | None:
        try:
            if ref.startswith("file:"):
                with open(ref[5:], "rb") as f:
                    return f.read()
            if ref.startswith("pref:"):
                raw = await self.prefs.get(PREFIX + "img." + ref[5:])
                return base64.b64decode(raw) if raw else None
        except Exception:
            return None
        return None

    async def delete_image(self, ref: str) -> None:
        if ref.startswith("file:"):
            try:
                os.remove(ref[5:])
            except OSError:
                pass
        elif ref.startswith("pref:"):
            await self.remove("img." + ref[5:])
