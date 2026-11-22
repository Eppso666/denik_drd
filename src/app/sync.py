"""Družina: propojení hráčů a Pána jeskyně.

Dva způsoby propojení (volí PJ při zakládání kampaně):
  • U stolu – telefon PJ je „stůl“: na stejné Wi-Fi k němu hráči připojí bez internetu a bez účtů (src/app/stul.py).
  • Vlastní server PJ – PJ si průvodcem založí bezplatný Supabase; hráči se připojí pozvánkou odkudkoli.

Oba způsoby mají stejné rozhraní (Backend), takže obrazovky ani logika kampaně nerozlišují, kde data jsou.
Kampaň patří vždy k jedné hře (DrD nebo DH). Postava je v ní jako kopie – originál zůstává v telefonu hráče.
Hráče do kampaně pouští PJ (schválení). PJ smí hráčům měnit životy a zkušenosti a posílat jim předměty a tajné
zprávy; změna se propíše do deníku hráče při další synchronizaci (i když byl zrovna offline).

Spojení se Supabase běží přes obyčejné HTTP dotazy (bez knihovny supabase-py), takže funguje na Androidu,
na PC i ve webové verzi (pyodide). Schéma databáze: supabase/schema.sql (v aplikaci app/schema.py).
"""
from __future__ import annotations

import asyncio
import base64
import datetime as dt
import hashlib
import json
import random
import secrets
import sys
import time
from typing import Any, Awaitable, Callable

try:  # výchozí server z dřívějších verzí (URL + publishable key); nový PJ si server nastaví průvodcem
    from . import config  # type: ignore
except ImportError:  # pragma: no cover
    config = None

CLIENT_READY = True
SCHEMA_VERSION = 2
SYNC_INTERVAL: float | None = 6.0  # s – jak často se při kampani stahují novinky (None = vypnuto, testy)
ONLINE_WINDOW = 90   # s – člen je „online“, když se ozval v posledních x sekundách
INVITE_BASE = "https://eppso666.github.io/denik_drd/"

# Bez 0/O, 1/I/L – kód se dobře přečte i nadiktuje.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
BUCKET = "campaign-images"
SHEET_KEYS = ("name", "race", "cls", "branch", "level", "alignment", "xp", "xp_next", "attrs", "hp", "hp_max", "mana",
              "mana_max", "mana_name", "items", "money", "skills", "abilities", "spells", "companions", "fatigue",
              "raw")
GM_NAME = "Pán jeskyně"


class NotConfigured(Exception):
    """Server pro družinu není nastavený."""


class SyncError(Exception):
    """Chyba serveru, srozumitelná pro uživatele. kind: down (server neodpovídá/spí), None (ostatní)."""

    def __init__(self, msg: str, kind: str | None = None):
        super().__init__(msg)
        self.kind = kind


# ----------------------------------------------------------------------------------- servery

def legacy_server() -> dict | None:
    """Server z config.py (kampaně z verze 0.12)."""
    url = getattr(config, "SUPABASE_URL", "") if config else ""
    key = getattr(config, "SUPABASE_KEY", "") if config else ""
    if not (CLIENT_READY and url and key):
        return None
    return {"kind": "own", "url": clean_url(url), "key": key}


def configured() -> bool:
    """Je k dispozici výchozí server (z config.py)?"""
    return legacy_server() is not None


def clean_url(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    for tail in ("/rest/v1", "/auth/v1"):
        if u.endswith(tail):
            u = u[: -len(tail)]
    if u and not u.startswith("http"):
        u = "https://" + u
    return u


def server_key(srv: dict) -> str:
    if srv.get("kind") == "table":
        return "table"
    return "own:" + clean_url(srv.get("url", ""))


def server_name(srv: dict | None) -> str:
    if not srv:
        return "bez propojení"
    if srv.get("kind") == "table":
        return "U stolu"
    return clean_url(srv.get("url", "")).removeprefix("https://")


def server_of(camp: dict | None) -> dict | None:
    if not camp:
        return None
    return camp.get("server") or (legacy_server() if is_remote(camp) else None)


def key_problem(key: str) -> str | None:
    """Tajný klíč do aplikace nepatří – vrátí důvod odmítnutí, jinak None."""
    k = (key or "").strip()
    if not k:
        return "Vlož Publishable key."
    if k.startswith("sb_secret_"):
        return "Tohle je tajný klíč (sb_secret_…). Do aplikace patří jen Publishable key (sb_publishable_…)."
    if k.count(".") == 2:  # starý klíč JWT – service_role nikdy
        try:
            part = k.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
            if claims.get("role") == "service_role":
                return "Tohle je tajný klíč service_role. Do aplikace patří jen veřejný klíč (anon / publishable)."
        except (ValueError, UnicodeDecodeError):
            pass
    return None


def new_pj_key(rng: random.Random | None = None) -> str:
    """Klíč PJ – zamkne server a přihlásí PJ na dalším zařízení (např. DRAK-7Q2M-K9XP)."""
    pick = (rng.choice if rng else secrets.choice)
    return "DRAK-" + "".join(pick(ALPHABET) for _ in range(4)) + "-" + "".join(pick(ALPHABET) for _ in range(4))


# ----------------------------------------------------------------------------------- pozvánky

def invite_payload(srv: dict, code: str) -> str:
    data = {"u": clean_url(srv["url"]), "k": srv["key"], "c": code}
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode().rstrip("=")


def invite_link(srv: dict, code: str) -> str:
    """Odkaz pro hráče: obsahuje adresu serveru PJ, veřejný klíč a kód kampaně."""
    return f"{INVITE_BASE}?pozvanka={invite_payload(srv, code)}"


def parse_invite(text: str) -> dict | None:
    """Z odkazu (nebo jen jeho části za pozvanka=) vrátí {"server": …, "code": …}."""
    t = (text or "").strip()
    if "pozvanka=" in t:
        t = t.split("pozvanka=", 1)[1].split("&", 1)[0].split("#", 1)[0]
    if not t or " " in t:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(t + "=" * (-len(t) % 4)).decode())
    except (ValueError, UnicodeDecodeError):
        return None
    code = normalize_code(str(data.get("c", "")))
    if not isinstance(data, dict) or not data.get("u") or not data.get("k") or code is None:
        return None
    return {"server": {"kind": "own", "url": clean_url(data["u"]), "key": data["k"]}, "code": code}


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


def is_table(camp: dict | None) -> bool:
    return bool(camp) and (camp.get("server") or {}).get("kind") == "table"


def base_campaign(system: str, **kw) -> dict:
    now = time.time()
    camp = {"name": "Nová kampaň", "system": system, "session": 1, "role": "gm", "status": "approved",
            "share_rolls": True, "share_hp": True, "hide_rolls": False, "locked": False, "joined": now,
            "synced": now, "members": [], "feed": [], "images": [], "saved_images": [], "messages": [],
            "online": False, "last_sync": 0}
    camp.update(kw)
    return camp


def gm_campaign(system: str, **kw) -> dict:
    """Kampaň v telefonu PJ (bez postavy): poznámky, mapy, souboj, zkušenosti k rozdělení."""
    kw.setdefault("role", "gm")
    camp = base_campaign(system, **kw)
    camp.update({"notes": [], "maps": [], "outbox": [], "sheets": {}, "xp_pool": [],
                 "combat": None, "notes_dirty": False, "created": time.time()})
    camp.update({k: v for k, v in kw.items()})
    return camp


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
    if not camp or not camp.get("share_rolls", True) or camp.get("status", "approved") != "approved":
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
            "hp": c.get("hp") if share else None, "hp_max": c.get("hp_max") if share else None,
            "avatar": None}


def sheet(c: dict) -> dict:
    """Kopie deníku pro PJ (bez poznámek, obrázků a historie)."""
    out = {k: c[k] for k in SHEET_KEYS if k in c}
    try:
        from . import model
        out["oc"] = model.oc_sheet(c)
    except Exception:  # pragma: no cover - neúplná postava
        pass
    return out


def is_online(member: dict, now: float | None = None) -> bool:
    ts = _parse_ts(member.get("last_seen"))
    return ts is not None and (now or time.time()) - ts < ONLINE_WINDOW


def players(camp: dict, status: str | None = "approved") -> list[dict]:
    return [m for m in camp.get("members") or [] if m.get("role") != "gm"
            and (status is None or m.get("status", "approved") == status)]


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


def apply_adjustment(c: dict, p: dict) -> str:
    """Úprava od PJ do deníku hráče. Vrátí krátký popis („Životy 12 → 9 · Zkušenosti +150“)."""
    from . import model

    parts: list[str] = []
    if p.get("hp") is not None:
        old = c.get("hp", 0)
        new = max(-99, min(int(p["hp"]), int(c.get("hp_max", 0)) + 99))
        c["hp"] = new
        if new != old:
            parts.append(f"Životy {old} → {new}")
    if p.get("hp_delta"):
        old = c.get("hp", 0)
        c["hp"] = old + int(p["hp_delta"])
        parts.append(f"Životy {old} → {c['hp']}")
    if p.get("xp"):
        c["xp"] = int(c.get("xp", 0)) + int(p["xp"])
        parts.append(f"Zkušenosti {int(p['xp']):+d}")
    for it in p.get("items") or []:
        c.setdefault("items", []).append(model.item(str(it.get("name", "Předmět"))[:80], it.get("category") or "Ostatní",
                                                    qty=int(it.get("qty", 1) or 1),
                                                    weight=float(it.get("weight", 0) or 0)))
        parts.append(f"Předmět: {it.get('name')}")
    return " · ".join(parts)


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


class Backend:
    """Společné rozhraní: vlastní server (Supabase) i stůl PJ (stul.py)."""

    uid: str | None = None

    async def create(self, name: str, system: str) -> dict: raise NotImplementedError
    async def join(self, code: str, system: str, char_id: str, snap: dict) -> dict: raise NotImplementedError
    async def leave(self, cid: str) -> None: raise NotImplementedError
    async def end(self, cid: str) -> None: raise NotImplementedError
    async def update_campaign(self, cid: str, fields: dict) -> None: raise NotImplementedError
    async def heartbeat(self, cid: str, snap: dict, share_rolls: bool, share_hp: bool) -> None: raise NotImplementedError
    async def put_sheet(self, cid: str, sh: dict) -> None: raise NotImplementedError
    async def add_rolls(self, cid: str, rows: list[dict]) -> None: raise NotImplementedError
    async def pull(self, cid: str, gm: bool) -> dict: raise NotImplementedError
    async def ack(self, cid: str, ids: list) -> None: raise NotImplementedError
    async def set_status(self, cid: str, uid: str, status: str) -> None: raise NotImplementedError
    async def kick(self, cid: str, uid: str) -> None: raise NotImplementedError
    async def adjust(self, cid: str, uid: str, payload: dict) -> None: raise NotImplementedError
    async def message(self, cid: str, uid: str, body: str) -> None: raise NotImplementedError
    async def member_sheet(self, cid: str, uid: str) -> dict | None: raise NotImplementedError
    async def share_image(self, cid: str, data: bytes, title: str) -> str: raise NotImplementedError
    async def download_image(self, path: str) -> bytes: raise NotImplementedError

    async def notes_get(self, cid: str) -> list | None:
        return None

    async def notes_put(self, cid: str, notes: list) -> None:
        return None


class Client(Backend):
    """Vlastní server PJ (Supabase). Přihlášení zařízení se ukládá do settings['auth'][klíč serveru]."""

    def __init__(self, settings: dict, save_settings: Callable[[], None], server: dict | None = None):
        self.settings = settings
        self.save_settings = save_settings
        srv = server or legacy_server() or {"kind": "own", "url": "", "key": ""}
        self.server = srv
        self.url = clean_url(srv.get("url", ""))
        self.key = srv.get("key", "")
        self.skey = server_key(srv)
        self._lock: asyncio.Lock | None = None
        legacy = legacy_server()
        if settings.get("sb_auth") and legacy and server_key(legacy) == self.skey:  # přihlášení z verze 0.12
            settings.setdefault("auth", {}).setdefault(self.skey, settings.pop("sb_auth"))

    # --- přihlášení ---------------------------------------------------------------
    @property
    def _auth(self) -> dict:
        return (self.settings.get("auth") or {}).get(self.skey) or {}

    @property
    def uid(self) -> str | None:  # type: ignore[override]
        return self._auth.get("uid")

    def _store_auth(self, data: dict) -> None:
        user = data.get("user") or {}
        self.settings.setdefault("auth", {})[self.skey] = {
            "access": data["access_token"], "refresh": data.get("refresh_token"),
            "exp": time.time() + float(data.get("expires_in", 3600)) - 60, "uid": user.get("id") or self.uid}
        self.save_settings()

    async def _send(self, method: str, url: str, headers: dict, body: bytes | None) -> tuple[int, bytes]:
        try:
            status, raw = await TRANSPORT(method, url, headers, body)
        except (OSError, asyncio.TimeoutError) as ex:
            raise SyncError("Server neodpovídá. Možná spí, nebo nejsi připojený k internetu.", "down") from ex
        if status in (502, 503, 504, 540, 544):
            raise SyncError("Server spí nebo se právě probouzí.", "down")
        return status, raw

    async def _auth_call(self, path: str, payload: dict) -> dict:
        status, raw = await self._send("POST", f"{self.url}/auth/v1/{path}",
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
        auth = self._auth
        if auth.get("access") and auth.get("exp", 0) > time.time():
            return auth["access"]
        if auth.get("refresh"):
            try:
                self._store_auth(await self._auth_call("token?grant_type=refresh_token",
                                                       {"refresh_token": auth["refresh"]}))
                return self._auth["access"]
            except SyncError as ex:
                if ex.kind == "down":
                    raise
        self._store_auth(await self._auth_call("signup", {"data": {}}))
        return self._auth["access"]

    # --- dotazy ------------------------------------------------------------------
    async def req(self, method: str, path: str, body: Any = None, prefer: str | None = None,
                  raw: bytes | None = None, content_type: str = "application/json", retry: bool = True) -> Any:
        token = await self.ensure_auth()
        headers = {"apikey": self.key, "Authorization": f"Bearer {token}", "Content-Type": content_type,
                   "Accept": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        status, resp = await self._send(method, self.url + path, headers, data)
        if status == 401 and retry:
            self.settings.setdefault("auth", {}).setdefault(self.skey, {})["exp"] = 0
            return await self.req(method, path, body, prefer, raw, content_type, retry=False)
        parsed = _json(resp)
        if status >= 400:
            msg = parsed.get("message") if isinstance(parsed, dict) else None
            if status == 404 and msg and "function" in msg.lower():
                msg = "Na serveru chybí nové databázové schéma. Spusť znovu skript z průvodce (krok 2)."
            raise SyncError(msg or f"Server odpověděl chybou {status}.")
        return parsed

    # --- průvodce a PJ -----------------------------------------------------------
    async def check(self) -> dict:
        """Kontrola pro průvodce: odpovídá server? je schéma? je zapnuté anonymní přihlášení?"""
        out = {"server": False, "db": False, "anon": False, "owned": False, "admin": False, "error": None}
        try:
            status, raw = await self._send("GET", f"{self.url}/auth/v1/settings", {"apikey": self.key}, None)
        except SyncError as ex:
            out["error"] = str(ex)
            return out
        if status in (401, 403):
            out["error"] = "Server klíč nepřijal – zkontroluj Publishable key."
            return out
        if status >= 400:
            out["error"] = f"Adresa nevypadá jako projekt Supabase ({status})."
            return out
        out["server"] = True
        out["anon"] = bool(((_json(raw) or {}).get("external") or {}).get("anonymous_users"))
        try:
            info = await self.req("POST", "/rest/v1/rpc/denik_info", {}) if out["anon"] else None
        except SyncError as ex:
            out["error"] = str(ex)
            return out
        if info is None:
            status, raw = await self._send("POST", f"{self.url}/rest/v1/rpc/denik_info",
                                           {"apikey": self.key, "Content-Type": "application/json"}, b"{}")
            info = _json(raw) if status < 400 else None
        if isinstance(info, dict) and int(info.get("version", 0)) >= SCHEMA_VERSION:
            out.update(db=True, owned=bool(info.get("owned")), admin=bool(info.get("admin")))
        elif not out["error"]:
            out["error"] = "Databáze ještě nemá tabulky Deníku – spusť skript z kroku 2."
        return out

    async def claim(self, pj_key: str) -> bool:
        return bool(await self.req("POST", "/rest/v1/rpc/claim_server", {"p_key": pj_key}))

    async def my_campaigns(self) -> list[dict]:
        return await self.req("GET", "/rest/v1/campaigns?select=id,name,system,code,session,locked"
                                     "&order=created_at.desc") or []

    # --- kampaň ------------------------------------------------------------------
    async def create(self, name: str, system: str) -> dict:
        return await self.req("POST", "/rest/v1/rpc/create_campaign",
                              {"p_name": name.strip()[:80] or "Nová kampaň", "p_system": system})

    async def join(self, code: str, system: str, char_id: str, snap: dict) -> dict:
        return await self.req("POST", "/rest/v1/rpc/join_campaign",
                              {"p_code": code, "p_system": system, "p_char_id": char_id, "p_snapshot": snap})

    async def leave(self, cid: str) -> None:
        await self.req("DELETE", f"/rest/v1/members?campaign_id=eq.{cid}&user_id=eq.{self.uid}")

    async def end(self, cid: str) -> None:
        await self.req("DELETE", f"/rest/v1/campaigns?id=eq.{cid}")

    async def update_campaign(self, cid: str, fields: dict) -> None:
        await self.req("PATCH", f"/rest/v1/campaigns?id=eq.{cid}", fields, prefer="return=minimal")

    async def heartbeat(self, cid: str, snap: dict, share_rolls: bool, share_hp: bool) -> None:
        await self.req("PATCH", f"/rest/v1/members?campaign_id=eq.{cid}&user_id=eq.{self.uid}",
                       {"snapshot": snap, "share_rolls": share_rolls, "share_hp": share_hp, "last_seen": _iso()},
                       prefer="return=minimal")

    async def put_sheet(self, cid: str, sh: dict) -> None:
        await self.req("POST", "/rest/v1/member_sheets", {"campaign_id": cid, "user_id": self.uid, "sheet": sh,
                                                          "updated_at": _iso()},
                       prefer="resolution=merge-duplicates,return=minimal")

    async def add_rolls(self, cid: str, rows: list[dict]) -> None:
        await self.req("POST", "/rest/v1/rolls", [dict(r, campaign_id=cid) for r in rows], prefer="return=minimal")

    async def pull(self, cid: str, gm: bool) -> dict:
        rows = await self.req("GET", f"/rest/v1/campaigns?id=eq.{cid}&select=name,session,code,locked,system")
        out: dict = {"campaign": rows[0] if rows else None}
        if not rows:
            return out
        out["members"] = await self.req(
            "GET", f"/rest/v1/members?campaign_id=eq.{cid}"
                   "&select=user_id,role,status,snapshot,last_seen,share_hp&order=role.asc")
        me = next((m for m in out["members"] if m.get("user_id") == self.uid), None)
        if not gm and (not me or me.get("status") != "approved"):
            return out
        out["feed"] = await self.req(
            "GET", f"/rest/v1/rolls_feed?campaign_id=eq.{cid}"
                   "&select=who,label,result,hidden,created_at&order=created_at.desc&limit=25")
        out["images"] = await self.req(
            "GET", f"/rest/v1/shared_images?campaign_id=eq.{cid}&select=id,title,path,created_at&order=created_at.desc")
        if gm:
            sheets = await self.req("GET", f"/rest/v1/member_sheets?campaign_id=eq.{cid}&select=user_id,sheet")
            out["sheets"] = {s["user_id"]: s["sheet"] for s in sheets or []}
        else:
            out["adjust"] = await self.req(
                "GET", f"/rest/v1/adjustments?campaign_id=eq.{cid}&user_id=eq.{self.uid}&applied=eq.false"
                       "&select=id,payload&order=id.asc")
            out["messages"] = await self.req(
                "GET", f"/rest/v1/messages?campaign_id=eq.{cid}&to_user=eq.{self.uid}"
                       "&select=id,body,created_at&order=created_at.desc&limit=10")
        return out

    async def ack(self, cid: str, ids: list) -> None:
        if ids:
            await self.req("PATCH", f"/rest/v1/adjustments?id=in.({','.join(str(i) for i in ids)})",
                           {"applied": True}, prefer="return=minimal")

    async def set_status(self, cid: str, uid: str, status: str) -> None:
        await self.req("PATCH", f"/rest/v1/members?campaign_id=eq.{cid}&user_id=eq.{uid}", {"status": status},
                       prefer="return=minimal")

    async def kick(self, cid: str, uid: str) -> None:
        await self.req("DELETE", f"/rest/v1/members?campaign_id=eq.{cid}&user_id=eq.{uid}")

    async def adjust(self, cid: str, uid: str, payload: dict) -> None:
        await self.req("POST", "/rest/v1/adjustments", {"campaign_id": cid, "user_id": uid, "payload": payload},
                       prefer="return=minimal")

    async def message(self, cid: str, uid: str, body: str) -> None:
        await self.req("POST", "/rest/v1/messages", {"campaign_id": cid, "to_user": uid, "body": body[:1000]},
                       prefer="return=minimal")

    async def member_sheet(self, cid: str, uid: str) -> dict | None:
        rows = await self.req("GET", f"/rest/v1/member_sheets?campaign_id=eq.{cid}&user_id=eq.{uid}&select=sheet")
        return rows[0]["sheet"] if rows else None

    async def share_image(self, cid: str, data: bytes, title: str) -> str:
        path = f"{cid}/{int(time.time() * 1000)}.jpg"
        await self.req("POST", f"/storage/v1/object/{BUCKET}/{path}", raw=data, content_type="image/jpeg")
        await self.req("POST", "/rest/v1/shared_images", {"campaign_id": cid, "title": title or "Obrázek",
                                                          "path": path}, prefer="return=minimal")
        return path

    async def download_image(self, path: str) -> bytes:
        token = await self.ensure_auth()
        status, data = await self._send("GET", f"{self.url}/storage/v1/object/authenticated/{BUCKET}/{path}",
                                        {"apikey": self.key, "Authorization": f"Bearer {token}"}, None)
        if status >= 400:
            raise SyncError("Obrázek se nepodařilo stáhnout.")
        return data

    async def notes_get(self, cid: str) -> list | None:
        rows = await self.req("GET", f"/rest/v1/gm_notes?campaign_id=eq.{cid}&select=notes")
        return rows[0]["notes"] if rows else None

    async def notes_put(self, cid: str, notes: list) -> None:
        await self.req("POST", "/rest/v1/gm_notes", {"campaign_id": cid, "notes": notes, "updated_at": _iso()},
                       prefer="resolution=merge-duplicates,return=minimal")


# ----------------------------------------------------------------------------------- synchronizace

async def sync_player(cl: Backend, c: dict) -> dict:
    """Hráč: odešle hody, stav a deník, stáhne družinu a použije úpravy od PJ.
    Vrátí {"changed": bool, "notice": text|None}."""
    camp = campaign(c)
    res: dict = {"changed": False, "notice": None}
    if not is_remote(camp):
        return res
    before = _state(camp)
    cid = camp["id"]
    approved = camp.get("status", "approved") == "approved"
    try:
        if approved:
            out = pending_rolls(c)
            if out:
                await cl.add_rolls(cid, [{"who": c["name"][:80], "label": str(h["label"])[:120],
                                          "result": str(h["value"])[:40], "hidden": False} for h in reversed(out)])
            camp["synced"] = max([camp.get("synced", 0), time.time() if not camp["share_rolls"] else 0]
                                 + [h.get("ts", 0) for h in out])
        await cl.heartbeat(cid, snapshot(c), camp.get("share_rolls", True), camp.get("share_hp", True))
        if approved:
            sh = sheet(c)
            digest = hashlib.sha1(json.dumps(sh, sort_keys=True, default=str).encode()).hexdigest()
            if digest != camp.get("sheet_hash"):
                await cl.put_sheet(cid, sh)
                camp["sheet_hash"] = digest
        data = await cl.pull(cid, gm=False)
        row = data.get("campaign")
        me = next((m for m in data.get("members") or [] if m.get("user_id") == cl.uid), None)
        if not row or not me:
            camp["gone"] = "rejected" if not approved else "removed"
        else:
            camp.update(name=row["name"], session=row["session"], code=row.get("code", camp.get("code")),
                        locked=row.get("locked", False))
            status = me.get("status", "approved")
            if status != camp.get("status"):
                camp["status"] = status
                if status == "approved":
                    res["notice"] = "PJ tě přijal do kampaně."
                    camp["synced"] = time.time()
            camp["members"] = data.get("members") or []
            if status == "approved":
                camp["feed"] = data.get("feed") or []
                camp["images"] = data.get("images") or []
                camp["messages"] = data.get("messages") or []
                done, texts = [], []
                for adj in data.get("adjust") or []:
                    txt = apply_adjustment(c, adj.get("payload") or {})
                    if txt:
                        texts.append(txt)
                    done.append(adj["id"])
                if done:
                    await cl.ack(cid, done)
                    camp["sheet_hash"] = None
                if texts:
                    camp["notice"] = {"text": " · ".join(texts), "ts": time.time()}
                    res["notice"] = "PJ ti upravil postavu: " + " · ".join(texts)
        camp["online"] = True
        camp["error"] = camp["error_kind"] = None
        camp["last_sync"] = time.time()
    except (SyncError, OSError, asyncio.TimeoutError) as ex:
        camp["online"] = False
        camp["error"] = str(ex) if isinstance(ex, SyncError) else "Bez připojení."
        camp["error_kind"] = getattr(ex, "kind", None) or "down"
    res["changed"] = before != _state(camp) or bool(res["notice"])
    return res


async def flush_outbox(cl: Backend, camp: dict) -> None:
    """Akce PJ (úpravy hráčů, zprávy, hody) – odešlou se, jakmile je spojení."""
    cid = camp["id"]
    while camp.get("outbox"):
        op = camp["outbox"][0]
        kind = op.get("op")
        if kind == "adjust":
            await cl.adjust(cid, op["uid"], op["payload"])
        elif kind == "message":
            await cl.message(cid, op["uid"], op["body"])
        elif kind == "roll":
            await cl.add_rolls(cid, [{"who": op.get("who", GM_NAME)[:80], "label": op["label"][:120],
                                      "result": str(op["result"])[:40], "hidden": bool(op.get("hidden"))}])
        camp["outbox"].pop(0)


async def sync_gm(cl: Backend, camp: dict) -> bool:
    """PJ: odešle čekající akce, stáhne hráče, deníky, hody a obrázky. Vrátí, zda se něco změnilo."""
    before = _state(camp)
    cid = camp["id"]
    try:
        await flush_outbox(cl, camp)
        await cl.heartbeat(cid, {"name": GM_NAME}, True, True)
        if camp.get("notes_dirty"):
            await cl.notes_put(cid, camp.get("notes") or [])
            camp["notes_dirty"] = False
        data = await cl.pull(cid, gm=True)
        row = data.get("campaign")
        if not row:
            camp["gone"] = True
        else:
            camp.update(name=row["name"], session=row["session"], code=row.get("code", camp.get("code")),
                        locked=row.get("locked", False))
            camp["members"] = data.get("members") or []
            camp["feed"] = data.get("feed") or []
            camp["images"] = data.get("images") or []
            camp["sheets"] = data.get("sheets") or {}
        camp["online"] = True
        camp["error"] = camp["error_kind"] = None
        camp["last_sync"] = time.time()
    except (SyncError, OSError, asyncio.TimeoutError) as ex:
        camp["online"] = False
        camp["error"] = str(ex) if isinstance(ex, SyncError) else "Bez připojení."
        camp["error_kind"] = getattr(ex, "kind", None) or "down"
    return before != _state(camp)


def gm_view_hp(camp: dict, m: dict) -> tuple[int | None, int | None]:
    """Životy hráče z pohledu PJ: z deníku (PJ vidí vždy), jinak ze sdíleného stavu."""
    sh = (camp.get("sheets") or {}).get(m.get("user_id")) or {}
    snap = m.get("snapshot") or {}
    hp = sh.get("hp", snap.get("hp"))
    hpm = sh.get("hp_max", snap.get("hp_max"))
    for op in camp.get("outbox") or []:  # ještě neodeslané úpravy
        if op.get("op") == "adjust" and op.get("uid") == m.get("user_id"):
            p = op["payload"]
            if p.get("hp") is not None:
                hp = p["hp"]
            if p.get("hp_delta") and hp is not None:
                hp += p["hp_delta"]
    return hp, hpm


def _state(camp: dict) -> str:
    return json.dumps([camp.get(k) for k in ("members", "feed", "images", "session", "online", "gone", "name",
                                             "status", "messages", "locked", "sheets", "error")],
                      sort_keys=True, default=str)


def _json(raw: bytes | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
