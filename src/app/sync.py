"""Družina a propojení hráčů přes Supabase (REST API, bez knihovny supabase-py).

Kampaň patří vždy k jedné hře (DrD nebo DH) a postava je v ní jako kopie – originál zůstává v telefonu.
Přihlášení je anonymní: každé zařízení si při prvním použití založí neviditelný účet.
Spojení běží přes obyčejné HTTP dotazy, takže funguje na Androidu, na PC i ve webové verzi (pyodide).
Bez internetu aplikace hraje dál; hody a změny životů se odešlou při další synchronizaci.

Schéma databáze a pravidla přístupu: supabase/schema.sql.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import json
import random
import sys
import time
from typing import Any, Awaitable, Callable

try:  # veřejné údaje projektu Supabase (URL + publishable key)
    from . import config  # type: ignore
except ImportError:  # pragma: no cover
    config = None

CLIENT_READY = True
SYNC_INTERVAL: float | None = 6.0  # s – jak často se při kampani stahují novinky (None = vypnuto, testy)
ONLINE_WINDOW = 90   # s – člen je „online“, když se ozval v posledních x sekundách

# Bez 0/O, 1/I/L – kód se dobře přečte i nadiktuje.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
BUCKET = "campaign-images"
SHEET_KEYS = ("name", "race", "cls", "branch", "level", "alignment", "xp", "attrs", "hp", "hp_max", "mana", "mana_max",
              "mana_name", "items", "money", "skills", "abilities", "spells", "companions", "fatigue", "raw")


class NotConfigured(Exception):
    """Server pro družinu není nastavený."""


class SyncError(Exception):
    """Chyba serveru, srozumitelná pro uživatele."""


def configured() -> bool:
    has_keys = bool(config and getattr(config, "SUPABASE_URL", "") and getattr(config, "SUPABASE_KEY", ""))
    return CLIENT_READY and has_keys


# ----------------------------------------------------------------------------------- místní část

def new_code(rng: random.Random | None = None) -> str:
    r = rng or random
    s = "".join(r.choice(ALPHABET) for _ in range(6))
    return f"{s[:3]}-{s[3:]}"


def normalize_code(text: str) -> str | None:
    """„k7p 42q“ → „K7P-42Q“; neplatný kód → None."""
    raw = "".join(ch for ch in (text or "").upper() if ch.isalnum())
    if len(raw) != 6 or any(ch not in ALPHABET for ch in raw):
        return None
    return f"{raw[:3]}-{raw[3:]}"


def campaign(c: dict) -> dict | None:
    return c.get("campaign")


def is_remote(camp: dict | None) -> bool:
    return bool(camp) and not str(camp.get("id", "")).startswith("local-")


def _base_campaign(c: dict, **kw) -> dict:
    now = time.time()
    camp = {"name": "Nová kampaň", "system": c["system"], "session": 1, "role": "gm", "share_rolls": True,
            "share_hp": True, "hide_rolls": False, "joined": now, "synced": now, "members": [], "feed": [],
            "images": [], "saved_images": [], "online": False, "last_sync": 0}
    camp.update(kw)
    return camp


def create_campaign(c: dict, name: str) -> dict:
    """Kampaň jen v tomto zařízení (bez serveru); zakladatel je PJ."""
    camp = _base_campaign(c, id=f"local-{int(time.time())}-{random.randint(1000, 9999)}",
                          name=name.strip() or "Nová kampaň", code=new_code())
    c["campaign"] = camp
    return camp


def join_campaign(c: dict, code: str) -> dict:
    """Bez serveru se ke kampani jiného zařízení připojit nedá (se serverem viz Client.join)."""
    if normalize_code(code) is None:
        raise ValueError("Kód má 6 znaků, např. K7P-42Q.")
    raise NotConfigured()


def leave(c: dict) -> None:
    c.pop("campaign", None)


def can_join(c: dict, camp_system: str) -> bool:
    """Kampaň patří k jedné hře: postava DH se nepřipojí do kampaně DrD a naopak."""
    return c.get("system") == camp_system


def rolls(c: dict) -> list[dict]:
    """Moje hody od připojení ke kampani (nejnovější první)."""
    camp = campaign(c)
    if not camp:
        return []
    return [h for h in c.get("history", []) if h.get("ts", 0) >= camp["joined"]]


def pending_rolls(c: dict) -> list[dict]:
    camp = campaign(c)
    if not camp or not camp.get("share_rolls", True):
        return []
    return [h for h in c.get("history", []) if h.get("ts", 0) > camp.get("synced", 0)]


def pending(c: dict) -> int:
    """Kolik hodů čeká na odeslání."""
    return len(pending_rolls(c))


def snapshot(c: dict) -> dict:
    """Co o postavě uvidí ostatní hráči (batoh a poznámky vidí jen hráč a PJ)."""
    camp = campaign(c) or {}
    share = camp.get("share_hp", True)
    return {"name": c["name"], "race": c.get("race"), "cls": c.get("cls"), "level": c.get("level"),
            "hp": c.get("hp") if share else None, "hp_max": c.get("hp_max") if share else None}


def sheet(c: dict) -> dict:
    """Kopie deníku pro PJ (bez poznámek, obrázků a historie)."""
    return {k: c[k] for k in SHEET_KEYS if k in c}


def is_online(member: dict, now: float | None = None) -> bool:
    ts = _parse_ts(member.get("last_seen"))
    return ts is not None and (now or time.time()) - ts < ONLINE_WINDOW


def _parse_ts(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _iso(ts: float | None = None) -> str:
    return dt.datetime.fromtimestamp(ts or time.time(), dt.timezone.utc).isoformat()


# ----------------------------------------------------------------------------------- HTTP

Transport = Callable[[str, str, dict, "bytes | None"], Awaitable[tuple[int, bytes]]]


async def _http(method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, bytes]:
    """HTTP dotaz: v prohlížeči přes fetch (pyodide), jinde přes urllib ve vedlejším vlákně."""
    if sys.platform == "emscripten":  # pragma: no cover - jen webová verze
        from pyodide.http import pyfetch  # type: ignore
        kw: dict[str, Any] = {"method": method, "headers": headers}
        if body is not None:
            from js import Uint8Array  # type: ignore
            kw["body"] = Uint8Array.new(body)
        resp = await pyfetch(url, **kw)
        return resp.status, await resp.bytes()

    import urllib.error
    import urllib.request

    def call() -> tuple[int, bytes]:
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
    return await asyncio.get_running_loop().run_in_executor(None, call)


TRANSPORT: Transport = _http


class Client:
    """Spojení se Supabase pro jedno zařízení. Přihlášení se ukládá do app.settings['sb_auth']."""

    def __init__(self, settings: dict, save_settings: Callable[[], None]):
        self.settings = settings
        self.save_settings = save_settings
        url = getattr(config, "SUPABASE_URL", "").rstrip("/")
        self.url = url[: -len("/rest/v1")] if url.endswith("/rest/v1") else url
        self.key = getattr(config, "SUPABASE_KEY", "")
        self._lock: asyncio.Lock | None = None

    # --- přihlášení ---------------------------------------------------------------
    @property
    def uid(self) -> str | None:
        return (self.settings.get("sb_auth") or {}).get("uid")

    def _store_auth(self, data: dict) -> None:
        user = data.get("user") or {}
        self.settings["sb_auth"] = {"access": data["access_token"], "refresh": data.get("refresh_token"),
                                    "exp": time.time() + float(data.get("expires_in", 3600)) - 60,
                                    "uid": user.get("id") or self.uid}
        self.save_settings()

    async def _auth_call(self, path: str, payload: dict) -> dict:
        status, raw = await TRANSPORT("POST", f"{self.url}/auth/v1/{path}",
                                      {"apikey": self.key, "Content-Type": "application/json"},
                                      json.dumps(payload).encode())
        data = _json(raw) or {}
        if status >= 400:
            msg = data.get("msg") or data.get("message") or data.get("error_description")
            if "anonymous" in str(msg).lower():
                msg = "Na serveru není zapnuté anonymní přihlášení (Authentication → Allow anonymous sign-ins)."
            raise SyncError(msg or f"Přihlášení selhalo ({status}).")
        return data

    async def ensure_auth(self) -> str:
        auth = self.settings.get("sb_auth") or {}
        if auth.get("access") and auth.get("exp", 0) > time.time():
            return auth["access"]
        if auth.get("refresh"):
            try:
                self._store_auth(await self._auth_call("token?grant_type=refresh_token",
                                                       {"refresh_token": auth["refresh"]}))
                return self.settings["sb_auth"]["access"]
            except SyncError:
                pass  # obnovení selhalo → nový anonymní účet
        self._store_auth(await self._auth_call("signup", {"data": {}}))
        return self.settings["sb_auth"]["access"]

    # --- dotazy ------------------------------------------------------------------
    async def req(self, method: str, path: str, body: Any = None, prefer: str | None = None,
                  raw: bytes | None = None, content_type: str = "application/json", retry: bool = True) -> Any:
        token = await self.ensure_auth()
        headers = {"apikey": self.key, "Authorization": f"Bearer {token}", "Content-Type": content_type,
                   "Accept": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        status, resp = await TRANSPORT(method, self.url + path, headers, data)
        if status == 401 and retry:
            self.settings.setdefault("sb_auth", {})["exp"] = 0
            return await self.req(method, path, body, prefer, raw, content_type, retry=False)
        parsed = _json(resp)
        if status >= 400:
            msg = parsed.get("message") if isinstance(parsed, dict) else None
            raise SyncError(msg or f"Server odpověděl chybou {status}.")
        return parsed

    # --- kampaň ------------------------------------------------------------------
    async def create(self, c: dict, name: str) -> dict:
        row = await self.req("POST", "/rest/v1/rpc/create_campaign", {
            "p_name": name.strip() or "Nová kampaň", "p_system": c["system"], "p_char_id": c["id"],
            "p_snapshot": snapshot(c)})
        c["campaign"] = _base_campaign(c, id=row["id"], name=row["name"], code=row["code"],
                                       session=row.get("session", 1), role="gm", uid=self.uid)
        await self.sync(c)
        return c["campaign"]

    async def join(self, c: dict, code: str) -> dict:
        norm = normalize_code(code)
        if norm is None:
            raise ValueError("Kód má 6 znaků, např. K7P-42Q.")
        row = await self.req("POST", "/rest/v1/rpc/join_campaign", {
            "p_code": norm, "p_system": c["system"], "p_char_id": c["id"], "p_snapshot": snapshot(c)})
        c["campaign"] = _base_campaign(c, id=row["id"], name=row["name"], code=row["code"],
                                       session=row.get("session", 1), role="player", uid=self.uid)
        await self.sync(c)
        return c["campaign"]

    async def leave(self, c: dict) -> None:
        camp = campaign(c)
        if is_remote(camp):
            if camp["role"] == "gm":  # PJ kampaň ukončí pro všechny
                await self.req("DELETE", f"/rest/v1/campaigns?id=eq.{camp['id']}")
            else:
                await self.req("DELETE", f"/rest/v1/members?campaign_id=eq.{camp['id']}&user_id=eq.{self.uid}")
        leave(c)

    async def set_session(self, c: dict, session: int) -> None:
        camp = c["campaign"]
        camp["session"] = max(1, session)
        if is_remote(camp) and camp["role"] == "gm":
            await self.req("PATCH", f"/rest/v1/campaigns?id=eq.{camp['id']}", {"session": camp["session"]},
                           prefer="return=minimal")

    async def member_sheet(self, camp: dict, user_id: str) -> dict | None:
        rows = await self.req("GET", f"/rest/v1/member_sheets?campaign_id=eq.{camp['id']}&user_id=eq.{user_id}"
                                     "&select=sheet")
        return rows[0]["sheet"] if rows else None

    async def share_image(self, c: dict, data: bytes, title: str) -> None:
        camp = c["campaign"]
        path = f"{camp['id']}/{int(time.time() * 1000)}.jpg"
        await self.req("POST", f"/storage/v1/object/{BUCKET}/{path}", raw=data, content_type="image/jpeg")
        await self.req("POST", "/rest/v1/shared_images", {"campaign_id": camp["id"], "title": title or "Obrázek",
                                                          "path": path}, prefer="return=minimal")
        camp.setdefault("saved_images", []).append(path)  # PJ ho v Deníku už má

    async def download_image(self, path: str) -> bytes:
        token = await self.ensure_auth()
        status, data = await TRANSPORT("GET", f"{self.url}/storage/v1/object/authenticated/{BUCKET}/{path}",
                                       {"apikey": self.key, "Authorization": f"Bearer {token}"}, None)
        if status >= 400:
            raise SyncError("Obrázek se nepodařilo stáhnout.")
        return data

    # --- Pán jeskyně (kampaň z Doupěte, bez postavy) ------------------------------------------
    async def gm_create(self, camp: dict) -> None:
        """Založí kampaň PJ na serveru; PJ je v ní jako člen „PJ“ bez postavy. Do camp zapíše sid a kód."""
        row = await self.req("POST", "/rest/v1/rpc/create_campaign", {
            "p_name": (camp.get("name") or "Nová kampaň")[:80], "p_system": camp["system"], "p_char_id": None,
            "p_snapshot": {"name": "Pán jeskyně"}})
        camp.update(sid=row["id"], code=row["code"], session=row.get("session", camp.get("session", 1)),
                    uid=self.uid)

    async def gm_pull(self, camp: dict) -> bool:
        """Stáhne hráče, jejich deníky a hody družiny. Vrátí, zda se něco změnilo."""
        sid = camp.get("sid")
        if not sid:
            return False
        before = json.dumps([camp.get("members"), camp.get("feed"), camp.get("sheets"), camp.get("online")],
                            sort_keys=True, default=str)
        try:
            await self.req("PATCH", f"/rest/v1/members?campaign_id=eq.{sid}&user_id=eq.{self.uid}",
                           {"last_seen": _iso()}, prefer="return=minimal")
            rows = await self.req("GET", f"/rest/v1/campaigns?id=eq.{sid}&select=name,session,code")
            if not rows:
                camp["gone"] = True
            else:
                camp["members"] = await self.req(
                    "GET", f"/rest/v1/members?campaign_id=eq.{sid}"
                           "&select=user_id,role,snapshot,last_seen,share_hp&order=role.asc")
                camp["feed"] = await self.req(
                    "GET", f"/rest/v1/rolls_feed?campaign_id=eq.{sid}"
                           "&select=who,label,result,hidden,created_at&order=created_at.desc&limit=25")
                sheets = await self.req("GET", f"/rest/v1/member_sheets?campaign_id=eq.{sid}&select=user_id,sheet")
                camp["sheets"] = {r["user_id"]: r["sheet"] for r in sheets or []}
            camp["online"] = True
            camp["error"] = None
            camp["last_sync"] = time.time()
        except (SyncError, OSError, asyncio.TimeoutError) as ex:
            camp["online"] = False
            camp["error"] = str(ex) if isinstance(ex, SyncError) else "Bez připojení k internetu."
        after = json.dumps([camp.get("members"), camp.get("feed"), camp.get("sheets"), camp.get("online")],
                           sort_keys=True, default=str)
        return before != after

    async def gm_update(self, camp: dict) -> None:
        if camp.get("sid"):
            await self.req("PATCH", f"/rest/v1/campaigns?id=eq.{camp['sid']}",
                           {"name": camp["name"][:80], "session": max(1, int(camp["session"]))},
                           prefer="return=minimal")

    async def gm_delete(self, camp: dict) -> None:
        if camp.get("sid"):
            await self.req("DELETE", f"/rest/v1/campaigns?id=eq.{camp['sid']}")

    async def gm_share_image(self, camp: dict, data: bytes, title: str) -> None:
        sid = camp["sid"]
        path = f"{sid}/{int(time.time() * 1000)}.jpg"
        await self.req("POST", f"/storage/v1/object/{BUCKET}/{path}", raw=data, content_type="image/jpeg")
        await self.req("POST", "/rest/v1/shared_images", {"campaign_id": sid, "title": title or "Obrázek",
                                                          "path": path}, prefer="return=minimal")

    async def gm_roll(self, camp: dict, label: str, result: str, hidden: bool) -> None:
        if camp.get("sid"):
            await self.req("POST", "/rest/v1/rolls", [{"campaign_id": camp["sid"], "who": "PJ", "label": label[:120],
                                                       "result": str(result)[:40], "hidden": hidden}],
                           prefer="return=minimal")

    # --- synchronizace -------------------------------------------------------------
    async def sync(self, c: dict) -> bool:
        """Odešle moje hody a stav postavy, stáhne členy, hody a obrázky. Vrátí, zda se něco změnilo."""
        camp = campaign(c)
        if not is_remote(camp):
            return False
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            before = _state(camp)
            cid = camp["id"]
            try:
                out = pending_rolls(c)
                if out:
                    hidden = camp["role"] == "gm" and camp.get("hide_rolls", False)
                    await self.req("POST", "/rest/v1/rolls", [
                        {"campaign_id": cid, "who": c["name"][:80], "label": str(h["label"])[:120],
                         "result": str(h["value"])[:40], "hidden": hidden} for h in reversed(out)],
                        prefer="return=minimal")
                camp["synced"] = max([camp.get("synced", 0), time.time() if not camp["share_rolls"] else 0]
                                     + [h.get("ts", 0) for h in out])
                await self.req("PATCH", f"/rest/v1/members?campaign_id=eq.{cid}&user_id=eq.{self.uid}", {
                    "snapshot": snapshot(c), "share_rolls": camp["share_rolls"], "share_hp": camp["share_hp"],
                    "last_seen": _iso()}, prefer="return=minimal")
                sh = sheet(c)
                digest = hashlib.sha1(json.dumps(sh, sort_keys=True, default=str).encode()).hexdigest()
                if digest != camp.get("sheet_hash"):
                    await self.req("POST", "/rest/v1/member_sheets", {"campaign_id": cid, "user_id": self.uid,
                                                                      "sheet": sh, "updated_at": _iso()},
                                   prefer="resolution=merge-duplicates,return=minimal")
                    camp["sheet_hash"] = digest
                rows = await self.req("GET", f"/rest/v1/campaigns?id=eq.{cid}&select=name,session,code")
                if not rows:
                    camp["gone"] = True
                else:
                    camp.update(name=rows[0]["name"], session=rows[0]["session"], code=rows[0]["code"])
                    camp["members"] = await self.req(
                        "GET", f"/rest/v1/members?campaign_id=eq.{cid}"
                               "&select=user_id,role,snapshot,last_seen,share_hp&order=role.asc")
                    camp["feed"] = await self.req(
                        "GET", f"/rest/v1/rolls_feed?campaign_id=eq.{cid}"
                               "&select=who,label,result,hidden,created_at&order=created_at.desc&limit=25")
                    camp["images"] = await self.req(
                        "GET", f"/rest/v1/shared_images?campaign_id=eq.{cid}"
                               "&select=id,title,path,created_at&order=created_at.desc")
                camp["online"] = True
                camp["error"] = None
                camp["last_sync"] = time.time()
            except (SyncError, OSError, asyncio.TimeoutError) as ex:
                camp["online"] = False
                camp["error"] = str(ex) if isinstance(ex, SyncError) else "Bez připojení k internetu."
            return before != _state(camp)


def _state(camp: dict) -> str:
    return json.dumps([camp.get(k) for k in ("members", "feed", "images", "session", "online", "gone", "name")],
                      sort_keys=True, default=str)


def _json(raw: bytes | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
