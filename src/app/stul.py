"""Hra u stolu: telefon PJ je stůl, hráči na stejné Wi-Fi se k němu připojí bez internetu a bez účtů.

Telefon (nebo PC) PJ spustí malý server v místní síti (port 47821). Hráči ho najdou hledáním v síti Wi-Fi
(nebo zadají čtyřmístný kód stolu) a pošlou žádost; PJ je přijme. Data jsou jen v telefonech u stolu.
Stav stolu se ukládá do kampaně v telefonu PJ, takže se příště otevře znovu.

Ve webové verzi (prohlížeč) stůl otevřít ani se k němu připojit nejde – prohlížeč spojení v místní síti
z https stránky nepovolí. Stůl funguje v aplikaci pro Android a na PC.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import random
import secrets
import socket
import sys
import time
from typing import Any, Callable

from . import sync

PORT = 47821
MAX_BODY = 3_000_000
TRANSPORT: sync.Transport | None = None   # testy: náhrada HTTP; None = skutečná síť
WEB_MSG = ("Ve webové verzi stůl nefunguje – prohlížeč spojení v síti Wi-Fi nepovolí. "
           "Použij aplikaci pro Android nebo PC, nebo vlastní server PJ.")


def supported() -> bool:
    return sys.platform != "emscripten"


def new_table_code(rng: random.Random | None = None) -> str:
    r = rng or random
    return f"{r.randint(1000, 9999)}"


class TableError(sync.SyncError):
    pass


# ----------------------------------------------------------------------------------- stav stolu (u PJ)

class TableState:
    """Kampaň u stolu: stejná pravidla jako na serveru (schvalování, skryté hody, úpravy od PJ)."""

    GM = "pj"

    def __init__(self, data: dict | None = None, **kw):
        d = data or {}
        self.d = {"id": d.get("id") or f"stul-{int(time.time())}-{random.randint(1000, 9999)}",
                  "name": d.get("name", kw.get("name", "Nová kampaň")), "system": d.get("system", kw.get("system", "drd")),
                  "code": d.get("code") or kw.get("code") or new_table_code(), "session": d.get("session", 1),
                  "locked": d.get("locked", False), "members": d.get("members") or {}, "sheets": d.get("sheets") or {},
                  "rolls": d.get("rolls") or [], "images": d.get("images") or [], "files": d.get("files") or {},
                  "adjust": d.get("adjust") or [], "messages": d.get("messages") or [], "n": d.get("n", 0),
                  "tokens": d.get("tokens") or {}}
        if self.GM not in self.d["members"]:
            self.d["members"][self.GM] = {"user_id": self.GM, "role": "gm", "status": "approved",
                                          "snapshot": {"name": sync.GM_NAME}, "last_seen": time.time(),
                                          "share_hp": True, "share_rolls": True}
        self.changed: Callable[[], None] | None = None

    @property
    def id(self) -> str:
        return self.d["id"]

    def dump(self) -> dict:
        return json.loads(json.dumps(self.d))

    def uid_for(self, token: str) -> str:
        uid = self.d["tokens"].get(token)
        if not uid:
            uid = "dev-" + hashlib.sha1(token.encode()).hexdigest()[:10]
            self.d["tokens"][token] = uid
        return uid

    def ping(self) -> dict:
        n = len([m for m in self.d["members"].values() if m["role"] != "gm" and m["status"] == "approved"])
        return {"app": "denik", "v": 1, "name": self.d["name"], "system": self.d["system"], "code": self.d["code"],
                "players": n, "locked": self.d["locked"]}

    def _next(self) -> int:
        self.d["n"] += 1
        return self.d["n"]

    def _member(self, uid: str) -> dict | None:
        return self.d["members"].get(uid)

    def _approved(self, uid: str) -> bool:
        m = self._member(uid)
        return bool(m) and m["status"] == "approved"

    def _gm(self, uid: str) -> bool:
        return uid == self.GM

    def _camp(self) -> dict:
        return {k: self.d[k] for k in ("id", "name", "system", "code", "session", "locked")}

    def handle(self, uid: str, op: str, a: dict) -> Any:
        """Jedna operace hráče nebo PJ. Výjimka TableError = srozumitelné odmítnutí."""
        fn = getattr(self, "op_" + op, None)
        if fn is None:
            raise TableError("Neznámá operace.")
        out = fn(uid, a or {})
        if op not in ("pull", "member_sheet", "download_image", "ping") and self.changed:
            self.changed()
        return out

    # --- operace -----------------------------------------------------------------
    def op_ping(self, uid, a):
        return self.ping()

    def op_join(self, uid, a):
        if str(a.get("code", "")) != self.d["code"]:
            raise TableError("Kód stolu nesedí.")
        if a.get("system") != self.d["system"]:
            raise TableError("Stůl je pro jinou hru – připoj se postavou pro %s." %
                             ("Dračí Hlídku" if self.d["system"] == "dh" else "Dračí doupě 1.6"))
        m = self._member(uid)
        if self.d["locked"] and not m:
            raise TableError("Kampaň je zamčená – PJ nové hráče nepřijímá.")
        if m:
            m.update(snapshot=a.get("snapshot") or {}, char_id=a.get("char_id"), last_seen=time.time())
        else:
            self.d["members"][uid] = {"user_id": uid, "role": "player", "status": "pending",
                                      "snapshot": a.get("snapshot") or {}, "char_id": a.get("char_id"),
                                      "last_seen": time.time(), "share_hp": True, "share_rolls": True}
        return self._camp()

    def op_leave(self, uid, a):
        self.d["members"].pop(uid, None)
        self.d["sheets"].pop(uid, None)

    def op_update_campaign(self, uid, a):
        if not self._gm(uid):
            raise TableError("Kampaň mění jen PJ.")
        for k in ("name", "session", "locked"):
            if k in a.get("fields", {}):
                self.d[k] = a["fields"][k]

    def op_heartbeat(self, uid, a):
        m = self._member(uid)
        if not m:
            return
        m.update(snapshot=a.get("snapshot") or m["snapshot"], share_rolls=bool(a.get("share_rolls", True)),
                 share_hp=bool(a.get("share_hp", True)), last_seen=time.time())

    def op_put_sheet(self, uid, a):
        if not self._approved(uid):
            raise TableError("Nejsi v kampani.")
        self.d["sheets"][uid] = a.get("sheet") or {}

    def op_add_rolls(self, uid, a):
        if not self._approved(uid):
            raise TableError("Nejsi v kampani.")
        for r in a.get("rows") or []:
            if r.get("hidden") and not self._gm(uid):
                raise TableError("Skrytě hází jen PJ.")
            self.d["rolls"].append({"who": str(r.get("who", ""))[:80], "label": str(r.get("label", ""))[:120],
                                    "result": str(r.get("result", ""))[:40], "hidden": bool(r.get("hidden")),
                                    "user_id": uid, "created_at": time.time()})
        self.d["rolls"] = self.d["rolls"][-200:]

    def op_pull(self, uid, a):
        gm = self._gm(uid)
        out: dict = {"campaign": self._camp() if self._member(uid) else None}
        if not out["campaign"]:
            return out
        ok = gm or self._approved(uid)
        mem = list(self.d["members"].values()) if ok else [self._member(uid)]
        out["members"] = [{k: m.get(k) for k in ("user_id", "role", "status", "snapshot", "last_seen", "share_hp")}
                          for m in mem]
        if not ok:
            return out
        feed = []
        for r in reversed(self.d["rolls"][-25:]):
            masked = r["hidden"] and r["user_id"] != uid and not gm
            feed.append({"who": r["who"], "label": "Skrytý hod" if masked else r["label"],
                         "result": "jen pro PJ" if masked else r["result"], "hidden": r["hidden"],
                         "created_at": r["created_at"]})
        out["feed"] = feed
        out["images"] = list(reversed(self.d["images"]))
        if gm:
            out["sheets"] = dict(self.d["sheets"])
        else:
            out["adjust"] = [{"id": x["id"], "payload": x["payload"]} for x in self.d["adjust"]
                             if x["user_id"] == uid and not x["applied"]]
            out["messages"] = [{"id": x["id"], "body": x["body"], "created_at": x["created_at"]}
                               for x in reversed(self.d["messages"]) if x["to_user"] == uid][:10]
        return out

    def op_ack(self, uid, a):
        for x in self.d["adjust"]:
            if x["id"] in (a.get("ids") or []) and x["user_id"] == uid:
                x["applied"] = True
        self.d["adjust"] = [x for x in self.d["adjust"] if not x["applied"]][-200:]

    def _need_gm(self, uid):
        if not self._gm(uid):
            raise TableError("Tohle smí jen PJ.")

    def op_set_status(self, uid, a):
        self._need_gm(uid)
        m = self._member(a.get("uid", ""))
        if m and m["role"] != "gm":
            m["status"] = a.get("status", "approved")

    def op_kick(self, uid, a):
        self._need_gm(uid)
        if a.get("uid") != self.GM:
            self.d["members"].pop(a.get("uid"), None)
            self.d["sheets"].pop(a.get("uid"), None)

    def op_adjust(self, uid, a):
        self._need_gm(uid)
        self.d["adjust"].append({"id": self._next(), "user_id": a["uid"], "payload": a.get("payload") or {},
                                 "applied": False})

    def op_message(self, uid, a):
        self._need_gm(uid)
        self.d["messages"].append({"id": self._next(), "to_user": a["uid"], "body": str(a.get("body", ""))[:1000],
                                   "created_at": time.time()})
        self.d["messages"] = self.d["messages"][-100:]

    def op_member_sheet(self, uid, a):
        if not (self._gm(uid) or a.get("uid") == uid):
            return None
        return self.d["sheets"].get(a.get("uid"))

    def op_share_image(self, uid, a):
        self._need_gm(uid)
        path = f"{self.id}/{int(time.time() * 1000)}.jpg"
        self.d["files"][path] = a.get("data", "")
        self.d["images"].append({"id": self._next(), "title": a.get("title") or "Obrázek", "path": path,
                                 "created_at": time.time()})
        while len(self.d["files"]) > 15:  # telefon PJ si drží jen posledních 15 obrázků
            old = self.d["images"].pop(0)
            self.d["files"].pop(old["path"], None)
        return path

    def op_download_image(self, uid, a):
        if not self._approved(uid):
            raise TableError("Nejsi v kampani.")
        data = self.d["files"].get(a.get("path"))
        if data is None:
            raise TableError("Obrázek na stole už není.")
        return data


# ----------------------------------------------------------------------------------- klienti

class _TableBackend(sync.Backend):
    async def _call(self, op: str, **a) -> Any:  # pragma: no cover - přepsáno
        raise NotImplementedError

    async def create(self, name, system):
        raise TableError("Stůl zakládá PJ v aplikaci.")

    async def join(self, code, system, char_id, snap):
        return await self._call("join", code=code, system=system, char_id=char_id, snapshot=snap)

    async def leave(self, cid):
        await self._call("leave")

    async def end(self, cid):
        return None

    async def update_campaign(self, cid, fields):
        await self._call("update_campaign", fields=fields)

    async def heartbeat(self, cid, snap, share_rolls, share_hp):
        await self._call("heartbeat", snapshot=snap, share_rolls=share_rolls, share_hp=share_hp)

    async def put_sheet(self, cid, sh):
        await self._call("put_sheet", sheet=sh)

    async def add_rolls(self, cid, rows):
        await self._call("add_rolls", rows=rows)

    async def pull(self, cid, gm):
        return await self._call("pull")

    async def ack(self, cid, ids):
        await self._call("ack", ids=ids)

    async def set_status(self, cid, uid, status):
        await self._call("set_status", uid=uid, status=status)

    async def kick(self, cid, uid):
        await self._call("kick", uid=uid)

    async def adjust(self, cid, uid, payload):
        await self._call("adjust", uid=uid, payload=payload)

    async def message(self, cid, uid, body):
        await self._call("message", uid=uid, body=body)

    async def member_sheet(self, cid, uid):
        return await self._call("member_sheet", uid=uid)

    async def share_image(self, cid, data, title):
        return await self._call("share_image", data=base64.b64encode(data).decode(), title=title)

    async def download_image(self, path):
        return base64.b64decode(await self._call("download_image", path=path))


class LocalTable(_TableBackend):
    """PJ u svého stolu – volá stav přímo, bez sítě."""

    def __init__(self, state: TableState):
        self.state = state
        self.uid = TableState.GM

    async def _call(self, op: str, **a) -> Any:
        return self.state.handle(self.uid, op, a)


class RemoteTable(_TableBackend):
    """Hráč u stolu – dotazy na telefon PJ v místní síti."""

    def __init__(self, settings: dict, save_settings: Callable[[], None], server: dict):
        self.settings = settings
        self.server = server
        tok = settings.get("table_token")
        if not tok:
            tok = settings["table_token"] = secrets.token_hex(16)
            save_settings()
        self.token = tok
        self.uid = "dev-" + hashlib.sha1(tok.encode()).hexdigest()[:10]

    async def _call(self, op: str, **a) -> Any:
        if not supported():
            raise TableError(WEB_MSG, "down")
        body = json.dumps({"token": self.token, "op": op, "args": a}).encode()
        send = TRANSPORT or sync._http
        try:
            status, raw = await send("POST", f"http://{self.server['host']}/api",
                                     {"Content-Type": "application/json"}, body)
        except (OSError, asyncio.TimeoutError) as ex:
            raise TableError("Stůl PJ nenalezen. Jsi na stejné Wi-Fi a má PJ otevřenou aplikaci?", "down") from ex
        data = sync._json(raw) or {}
        if status >= 400 or "error" in data:
            raise TableError(data.get("error") or f"Stůl odpověděl chybou {status}.")
        return data.get("result")


# ----------------------------------------------------------------------------------- server v telefonu PJ

class Host:
    """Malý HTTP server stolu (jen místní síť)."""

    def __init__(self, state: TableState):
        self.state = state
        self.server: asyncio.AbstractServer | None = None
        self.port = PORT
        self.error: str | None = None

    @property
    def running(self) -> bool:
        return self.server is not None

    async def start(self, port: int = PORT, host: str = "0.0.0.0") -> bool:
        if self.server or not supported():
            self.error = None if self.server else WEB_MSG
            return self.server is not None
        try:
            self.server = await asyncio.start_server(self._client, host, port)
            self.port = self.server.sockets[0].getsockname()[1]
            self.error = None
            return True
        except OSError as ex:
            self.error = f"Stůl se nepodařilo otevřít ({ex.strerror or ex})."
            return False

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception:  # pragma: no cover
                pass
            self.server = None

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            head = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 10)
            lines = head.decode("latin-1").split("\r\n")
            method, path = (lines[0].split(" ") + ["", ""])[:2]
            headers = {ln.split(":", 1)[0].strip().lower(): ln.split(":", 1)[1].strip()
                       for ln in lines[1:] if ":" in ln}
            size = min(int(headers.get("content-length", "0") or 0), MAX_BODY)
            body = await asyncio.wait_for(reader.readexactly(size), 20) if size else b""
            status, out = self.route(method, path, body)
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, asyncio.TimeoutError, ValueError):
            status, out = 400, {"error": "Špatný dotaz."}
        except Exception as ex:  # pragma: no cover - server nesmí spadnout
            status, out = 500, {"error": str(ex)}
        data = json.dumps(out).encode()
        writer.write(b"HTTP/1.1 %d OK\r\nContent-Type: application/json\r\nContent-Length: %d\r\n"
                     b"Access-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n" % (status, len(data)) + data)
        try:
            await writer.drain()
            writer.close()
        except Exception:  # pragma: no cover
            pass

    def route(self, method: str, path: str, body: bytes) -> tuple[int, dict]:
        if method == "GET" and path.startswith("/ping"):
            return 200, self.state.ping()
        if method == "POST" and path.startswith("/api"):
            req = json.loads(body.decode() or "{}")
            uid = self.state.uid_for(str(req.get("token", ""))[:64] or "anon")
            try:
                return 200, {"result": self.state.handle(uid, str(req.get("op", "")), req.get("args") or {})}
            except TableError as ex:
                return 200, {"error": str(ex)}
        return 404, {"error": "Neznámá adresa."}


# ----------------------------------------------------------------------------------- hledání stolu

def local_ip() -> str | None:
    """Adresa telefonu v síti Wi-Fi (bez odeslání dat – jen zjištění trasy)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.254.254.254", 1))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


async def ping(host: str, timeout: float = 0.8) -> dict | None:
    try:
        h, _, p = host.partition(":")
        reader, writer = await asyncio.wait_for(asyncio.open_connection(h, int(p or PORT)), timeout)
    except (OSError, asyncio.TimeoutError, ValueError):
        return None
    try:
        writer.write(b"GET /ping HTTP/1.0\r\nHost: stul\r\n\r\n")
        await writer.drain()
        raw = await asyncio.wait_for(reader.read(4096), timeout * 2)
        writer.close()
        data = json.loads(raw.split(b"\r\n\r\n", 1)[1].decode())
        if data.get("app") == "denik":
            data["host"] = host if ":" in host else f"{host}:{PORT}"
            return data
    except Exception:
        return None
    return None


async def find_tables(hosts: list[str] | None = None, timeout: float = 0.8) -> list[dict]:
    """Projde místní síť (stejná podsíť /24) a vrátí nalezené stoly."""
    if not supported():
        raise TableError(WEB_MSG)
    if hosts is None:
        ip = local_ip()
        if not ip:
            raise TableError("Telefon není připojený k Wi-Fi (ani k hotspotu PJ).")
        base = ip.rsplit(".", 1)[0]
        hosts = [f"{base}.{i}" for i in range(1, 255)]
    sem = asyncio.Semaphore(64)

    async def one(h: str):
        async with sem:
            return await ping(h, timeout)
    found = [r for r in await asyncio.gather(*(one(h) for h in hosts)) if r]
    return found
