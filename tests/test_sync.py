"""Družina: vlastní server PJ (falešný Supabase v paměti) a hra u stolu (stav stolu, HTTP server v síti)."""
import asyncio
import json
import re
import time
import urllib.parse as up

import pytest

from app import model, schema, stul, sync

URL = "https://abcdefghijkl.supabase.co"
SRV = {"kind": "own", "url": URL, "key": "sb_publishable_test"}


class FakeSupabase:
    """Zjednodušený Supabase s pravidly jako v supabase/schema.sql (verze 2)."""

    def __init__(self):
        self.users = {}
        self.campaigns = []
        self.members = []
        self.sheets = []
        self.rolls = []
        self.images = []
        self.files = {}
        self.adjust = []
        self.messages = []
        self.notes = {}
        self.owner_key = None
        self.admins = set()
        self.n = 0
        self.anonymous = True
        self.schema = True
        self.asleep = False

    def _uid(self, headers):
        tok = headers.get("Authorization", "").removeprefix("Bearer ")
        return self.users.get(tok)

    def _member(self, cid, uid, any_status=False):
        m = next((m for m in self.members if m["campaign_id"] == cid and m["user_id"] == uid), None)
        if m and (any_status or m["status"] == "approved"):
            return m
        return None

    def is_admin(self, uid):
        return uid in self.admins

    def is_member(self, cid, uid):
        return self.is_admin(uid) or bool(self._member(cid, uid))

    def is_gm(self, cid, uid):
        m = self._member(cid, uid, True)
        return self.is_admin(uid) or bool(m and m["role"] == "gm")

    @staticmethod
    def ok(data=None, status=200):
        return status, json.dumps(data, default=str).encode() if data is not None else b""

    @staticmethod
    def err(msg, status=400):
        return status, json.dumps({"message": msg}).encode()

    async def __call__(self, method, url, headers, body):
        if self.asleep:
            raise OSError("server spí")
        u = up.urlparse(url)
        assert u.scheme + "://" + u.netloc == URL
        path, q = u.path, dict(up.parse_qsl(u.query))
        data = json.loads(body) if body and headers.get("Content-Type") == "application/json" else body
        if path == "/auth/v1/settings":
            return self.ok({"external": {"anonymous_users": self.anonymous}})
        if path == "/auth/v1/signup":
            if not self.anonymous:
                return 422, b'{"msg":"Anonymous sign-ins are disabled"}'
            self.n += 1
            uid, tok = f"user-{self.n}", f"tok-{self.n}"
            self.users[tok] = uid
            return self.ok({"access_token": tok, "refresh_token": "r" + tok, "expires_in": 3600, "user": {"id": uid}})
        if path.startswith("/auth/"):
            return 400, b'{"msg":"invalid refresh"}'
        if not self.schema and path.startswith("/rest/v1/rpc/"):
            return 404, b'{"message":"Could not find the function public.denik_info"}'
        uid = self._uid(headers)
        if path == "/rest/v1/rpc/denik_info":
            return self.ok({"version": 2, "owned": self.owner_key is not None, "admin": self.is_admin(uid)})
        if uid is None:
            return 401, b'{"message":"JWT expired"}'
        eq = {k: v.removeprefix("eq.") for k, v in q.items() if v.startswith("eq.")}
        cid = eq.get("campaign_id") or eq.get("id")
        if path == "/rest/v1/rpc/claim_server":
            if self.owner_key is None:
                self.owner_key = data["p_key"]
            elif self.owner_key != data["p_key"]:
                return self.ok(False)
            self.admins.add(uid)
            return self.ok(True)
        if path == "/rest/v1/rpc/create_campaign":
            if not self.is_admin(uid):
                return self.err("Kampaň na tomto serveru zakládá jen jeho PJ.")
            self.n += 1
            camp = {"id": f"camp-{self.n}", "name": data["p_name"], "system": data["p_system"],
                    "code": sync.new_code(), "session": 1, "gm": uid, "locked": False}
            self.campaigns.append(camp)
            self.members.append({"campaign_id": camp["id"], "user_id": uid, "role": "gm", "status": "approved",
                                 "snapshot": {"name": "Pán jeskyně"}, "last_seen": time.time(), "share_hp": True})
            return self.ok(camp)
        if path == "/rest/v1/rpc/join_campaign":
            camp = next((c for c in self.campaigns if c["code"] == data["p_code"]), None)
            if not camp:
                return self.err("Kampaň s tímto kódem neexistuje.")
            if camp["system"] != data["p_system"]:
                return self.err("Kampaň je pro jinou hru.")
            m = self._member(camp["id"], uid, True)
            if camp["locked"] and not m:
                return self.err("Kampaň je zamčená – PJ nové hráče nepřijímá.")
            if m:
                m["snapshot"] = data["p_snapshot"]
            else:
                self.members.append({"campaign_id": camp["id"], "user_id": uid, "role": "player", "status": "pending",
                                     "snapshot": data["p_snapshot"], "last_seen": time.time(), "share_hp": True})
            return self.ok(camp)
        if path.startswith("/storage/v1/object/"):
            p = re.sub(r"^/storage/v1/object/(authenticated/)?campaign-images/", "", path)
            c = p.split("/")[0]
            if method == "POST":
                if not self.is_gm(c, uid):
                    return self.err("forbidden", 403)
                self.files[p] = body
                return self.ok({})
            return (200, self.files[p]) if self.is_member(c, uid) and p in self.files else (404, b"")
        table = path.removeprefix("/rest/v1/")
        if table == "campaigns":
            rows = [c for c in self.campaigns if (cid is None or c["id"] == cid)
                    and (self.is_member(c["id"], uid) or self._member(c["id"], uid, True))]
            if method == "GET":
                return self.ok(rows)
            for c in rows:
                if not self.is_gm(c["id"], uid):
                    continue
                if method == "PATCH":
                    c.update(data)
                if method == "DELETE":
                    self.campaigns.remove(c)
                    self.members = [m for m in self.members if m["campaign_id"] != c["id"]]
            return self.ok(None, 204)
        if table == "members":
            if method == "GET":
                return self.ok([m for m in self.members if m["campaign_id"] == cid
                                and (self.is_member(cid, uid) or m["user_id"] == uid)])
            target = eq["user_id"]
            m = self._member(cid, target, True)
            if method == "PATCH" and m and (target == uid or self.is_gm(cid, uid)):
                if not self.is_gm(cid, uid):
                    data = {k: v for k, v in data.items() if k not in ("status", "role")}
                m.update(data)
            if method == "DELETE" and m and (target == uid or self.is_gm(cid, uid)):
                self.members.remove(m)
            return self.ok(None, 204)
        if table == "member_sheets":
            if method == "POST":
                if not self.is_member(data["campaign_id"], uid):
                    return self.err("rls", 403)
                self.sheets = [s for s in self.sheets if not (s["campaign_id"] == data["campaign_id"]
                                                              and s["user_id"] == uid)]
                self.sheets.append(dict(data, user_id=uid))
                return self.ok(None, 201)
            return self.ok([s for s in self.sheets if s["campaign_id"] == cid
                            and (eq.get("user_id") in (None, s["user_id"]))
                            and (self.is_gm(cid, uid) or s["user_id"] == uid)])
        if table == "rolls":
            for r in data:
                if not self.is_member(r["campaign_id"], uid) or (r["hidden"] and not self.is_gm(r["campaign_id"], uid)):
                    return self.err("rls", 403)
                self.rolls.append(dict(r, user_id=uid, created_at=time.time()))
            return self.ok(None, 201)
        if table == "rolls_feed":
            gm = self.is_gm(cid, uid)
            rows = []
            for r in reversed(self.rolls):
                if r["campaign_id"] != cid or not self.is_member(cid, uid):
                    continue
                masked = r["hidden"] and r["user_id"] != uid and not gm
                rows.append({"who": r["who"], "label": "Skrytý hod" if masked else r["label"],
                             "result": "jen pro PJ" if masked else r["result"], "hidden": r["hidden"],
                             "created_at": r["created_at"]})
            return self.ok(rows)
        if table == "shared_images":
            if method == "POST":
                self.images.append(dict(data, id=len(self.images) + 1, created_at=time.time()))
                return self.ok(None, 201)
            return self.ok([i for i in self.images if i["campaign_id"] == cid and self.is_member(cid, uid)])
        if table == "adjustments":
            if method == "POST":
                if not self.is_gm(data["campaign_id"], uid):
                    return self.err("rls", 403)
                self.n += 1
                self.adjust.append(dict(data, id=self.n, applied=False))
                return self.ok(None, 201)
            if method == "PATCH":
                ids = {int(x) for x in q["id"].removeprefix("in.(").rstrip(")").split(",")}
                for a in self.adjust:
                    if a["id"] in ids and (a["user_id"] == uid or self.is_gm(a["campaign_id"], uid)):
                        a["applied"] = True
                return self.ok(None, 204)
            return self.ok([{"id": a["id"], "payload": a["payload"]} for a in self.adjust
                            if a["campaign_id"] == cid and a["user_id"] == eq.get("user_id") == uid
                            and not a["applied"]])
        if table == "messages":
            if method == "POST":
                if not self.is_gm(data["campaign_id"], uid):
                    return self.err("rls", 403)
                self.n += 1
                self.messages.append(dict(data, id=self.n, created_at=time.time()))
                return self.ok(None, 201)
            return self.ok([m for m in reversed(self.messages) if m["campaign_id"] == cid and m["to_user"] == uid])
        if table == "gm_notes":
            if not self.is_gm(cid or (data or {}).get("campaign_id"), uid):
                return self.ok([]) if method == "GET" else self.err("rls", 403)
            if method == "POST":
                self.notes[data["campaign_id"]] = data["notes"]
                return self.ok(None, 201)
            return self.ok([{"notes": self.notes[cid]}] if cid in self.notes else [])
        return self.err("unknown", 404)


def _client(settings, srv=SRV):
    return sync.Client(settings, lambda: None, srv)


def _gm_camp(row, cl):
    return sync.gm_campaign(row["system"], id=row["id"], name=row["name"], code=row["code"], server=SRV, uid=cl.uid)


async def _join(cl, c, code, srv=SRV):
    row = await cl.join(code, c["system"], c["id"], sync.snapshot(c))
    c["campaign"] = sync.base_campaign(row["system"], id=row["id"], name=row["name"], code=row["code"],
                                       role="player", status="pending", server=srv)
    return await sync.sync_player(cl, c)


def test_own_server_flow(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    pj, pj2, stranger, pl, late = _client({}), _client({}), _client({}), _client({}), _client({})
    elwin = model.create_character("drd", "Elwin", "Elf", "Hraničář", [10, 14, 11, 13, 12])
    gorm = model.create_character("dh", "Gorm", "Trpaslík", "Válečník", [18, 9, 19, 10, 7])
    kira = model.create_character("drd", "Kira", "Kudůk", "Zloděj", [5, 16, 10, 12, 14])

    async def scenario():
        # průvodce: kontrola serveru a zamčení klíčem PJ
        chk = await pj.check()
        assert chk["server"] and chk["db"] and chk["anon"] and not chk["owned"]
        key = sync.new_pj_key()
        assert await pj.claim(key) and not await stranger.claim(sync.new_pj_key())
        with pytest.raises(sync.SyncError, match="jen jeho PJ"):
            await stranger.create("Moje", "drd")
        row = await pj.create("Prokletí Černé věže", "drd")
        camp = _gm_camp(row, pj)
        await sync.sync_gm(pj, camp)
        assert camp["online"] and sync.players(camp) == []

        # hráč požádá – čeká na schválení, nevidí hody ani ostatní
        with pytest.raises(sync.SyncError, match="jinou hru"):
            await pl.join(camp["code"], "dh", gorm["id"], sync.snapshot(gorm))
        res = await _join(pl, elwin, camp["code"])
        assert elwin["campaign"]["status"] == "pending" and not res["notice"]
        await sync.sync_gm(pj, camp)
        assert [m["snapshot"]["name"] for m in sync.players(camp, "pending")] == ["Elwin"]
        model.add_history(elwin, "Útok", "16")
        assert sync.pending(elwin) == 0  # čekající hráč hody neodesílá

        # PJ přijme, hráč dostane zprávu „PJ tě přijal“
        await pj.set_status(camp["id"], pl.uid, "approved")
        res = await sync.sync_player(pl, elwin)
        assert elwin["campaign"]["status"] == "approved" and "přijal" in res["notice"]
        model.add_history(elwin, "Útok", "17")
        await sync.sync_player(pl, elwin)
        # PJ: skrytý hod, úprava životů a zkušeností, předmět, zpráva
        camp["outbox"] += [{"op": "roll", "label": "Past", "result": "5", "hidden": True},
                           {"op": "adjust", "uid": pl.uid, "payload": {"hp": 3, "xp": 150,
                                                                        "items": [{"name": "Lektvar", "qty": 2}]}},
                           {"op": "message", "uid": pl.uid, "body": "Všimneš si černé pečeti."}]
        await sync.sync_gm(pj, camp)
        assert camp["outbox"] == [] and camp["sheets"][pl.uid]["name"] == "Elwin"
        hp_max = elwin["hp_max"]
        res = await sync.sync_player(pl, elwin)
        assert elwin["hp"] == 3 and elwin["xp"] == 150 and any(i["name"] == "Lektvar" for i in elwin["items"])
        assert f"Životy {hp_max} → 3" in res["notice"] and "+150" in res["notice"]
        assert elwin["campaign"]["messages"][0]["body"] == "Všimneš si černé pečeti."
        feed = {r["label"]: r["result"] for r in elwin["campaign"]["feed"]}
        assert feed["Útok"] == "17" and feed["Skrytý hod"] == "jen pro PJ"
        await sync.sync_player(pl, elwin)  # úprava se použije jen jednou
        assert elwin["xp"] == 150
        # hráč si nemůže sám změnit stav, nevidí poznámky PJ
        camp["notes"] = [{"title": "Zrádce", "text": "Hostinský"}]
        camp["notes_dirty"] = True
        await sync.sync_gm(pj, camp)
        assert await pl.notes_get(camp["id"]) is None

        # zámek: nový hráč se nepřipojí
        await pj.update_campaign(camp["id"], {"locked": True})
        with pytest.raises(sync.SyncError, match="zamčená"):
            await late.join(camp["code"], "drd", kira["id"], sync.snapshot(kira))

        # druhé zařízení PJ: klíčem PJ, kampaně i poznámky
        assert await pj2.claim(key)
        mine = await pj2.my_campaigns()
        assert [r["id"] for r in mine] == [camp["id"]] and (await pj2.notes_get(camp["id"]))[0]["title"] == "Zrádce"

        # obrázek od PJ
        path = await pj.share_image(camp["id"], b"JPEG", "Mapa")
        await sync.sync_player(pl, elwin)
        assert elwin["campaign"]["images"][0]["title"] == "Mapa" and await pl.download_image(path) == b"JPEG"
        with pytest.raises(sync.SyncError):
            await pl.share_image(camp["id"], b"x", "hack")

        # vyloučení: hráč kampaň ztratí, postava zůstane
        await pj.kick(camp["id"], pl.uid)
        await sync.sync_player(pl, elwin)
        assert elwin["campaign"]["gone"] == "removed"

        # ukončení kampaně
        await pj.end(camp["id"])
        await sync.sync_gm(pj, camp)
        assert camp["gone"] and not srv.campaigns

    asyncio.run(scenario())


def test_server_problems(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    cl = _client({})
    srv.anonymous = False
    chk = asyncio.run(cl.check())
    assert chk["server"] and not chk["anon"]
    with pytest.raises(sync.SyncError, match="anonymní"):
        asyncio.run(cl.ensure_auth())
    srv.anonymous, srv.schema = True, False
    chk = asyncio.run(cl.check())
    assert chk["server"] and not chk["db"] and chk["error"]
    # uspaný server
    srv.schema, srv.asleep = True, True
    chk = asyncio.run(cl.check())
    assert not chk["server"] and "neodpovídá" in chk["error"]
    camp = sync.gm_campaign("drd", id="x", name="X", code="AAA-BBB", server=SRV)
    asyncio.run(sync.sync_gm(cl, camp))
    assert camp["online"] is False and camp["error_kind"] == "down"
    # tajný klíč aplikace odmítne
    assert sync.key_problem("sb_secret_abc") and sync.key_problem("") and not sync.key_problem("sb_publishable_x")


def test_offline_queue(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    pj, pl = _client({}), _client({})
    c = model.create_character("drd", "Elwin", "Elf", "Hraničář", [10, 14, 11, 13, 12])

    async def run():
        await pj.claim(sync.new_pj_key())
        camp = _gm_camp(await pj.create("Doly", "drd"), pj)
        await _join(pl, c, camp["code"])
        await pj.set_status(camp["id"], pl.uid, "approved")
        await sync.sync_player(pl, c)
        srv.asleep = True
        model.add_history(c, "Útok", "9")
        camp["outbox"].append({"op": "adjust", "uid": pl.uid, "payload": {"xp": 50}})
        await sync.sync_player(pl, c)
        await sync.sync_gm(pj, camp)
        assert not c["campaign"]["online"] and sync.pending(c) == 1 and len(camp["outbox"]) == 1
        srv.asleep = False
        await sync.sync_gm(pj, camp)
        await sync.sync_player(pl, c)
        assert c["campaign"]["online"] and sync.pending(c) == 0 and c["xp"] == 50 and not camp["outbox"]
    asyncio.run(run())


def test_auth_refresh_and_legacy(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    settings = {}
    cl = _client(settings)
    asyncio.run(cl.ensure_auth())
    uid = cl.uid
    settings["auth"][sync.server_key(SRV)]["exp"] = 0  # refresh selže → nový účet, ale nespadne
    asyncio.run(cl.ensure_auth())
    assert cl.uid and uid
    # přihlášení z verze 0.12 se převede pod klíč výchozího serveru
    legacy = sync.legacy_server()
    s2 = {"sb_auth": {"access": "a", "exp": time.time() + 99, "uid": "u-old"}}
    c2 = sync.Client(s2, lambda: None, legacy)
    assert c2.uid == "u-old" and "sb_auth" not in s2


def test_invites_and_schema():
    link = sync.invite_link(SRV, "K7P-42Q")
    assert link.startswith(sync.INVITE_BASE)
    inv = sync.parse_invite(link)
    assert inv["code"] == "K7P-42Q" and inv["server"]["url"] == URL and inv["server"]["key"] == SRV["key"]
    assert sync.parse_invite("pozvanka=" + link.split("pozvanka=")[1]) == inv
    assert sync.parse_invite("nesmysl") is None and sync.parse_invite("") is None
    assert len(sync.new_pj_key()) == 14 and sync.new_pj_key().startswith("DRAK-")
    assert sync.clean_url("abcdefghijkl.supabase.co/rest/v1/") == URL
    with open("supabase/schema.sql", encoding="utf-8") as fh:
        assert fh.read() == schema.SCHEMA, "app/schema.py neodpovídá supabase/schema.sql"
    from app import qr
    png = qr.png(link)
    assert png and png.startswith(b"\x89PNG")


# ------------------------------------------------------------------------------------- u stolu

def _table(monkeypatch):
    state = stul.TableState(name="Doly pod Černou horou", system="dh")
    host = stul.Host(state)

    async def transport(method, url, headers, body):
        status, out = host.route(method, up.urlparse(url).path, body or b"")
        return status, json.dumps(out).encode()
    monkeypatch.setattr(stul, "TRANSPORT", transport)
    return state, host


def test_table_flow(monkeypatch):
    state, host = _table(monkeypatch)
    pj = stul.LocalTable(state)
    srv = {"kind": "table", "host": "192.168.1.5:47821", "code": state.d["code"]}
    p1 = stul.RemoteTable({}, lambda: None, srv)
    p2 = stul.RemoteTable({}, lambda: None, srv)
    thor = model.create_character("dh", "Thorgrim", "Trpaslík", "Válečník", [18, 9, 19, 10, 7])
    elwin = model.create_character("drd", "Elwin", "Elf", "Hraničář", [10, 14, 11, 13, 12])
    camp = sync.gm_campaign("dh", id=state.id, name=state.d["name"], code=state.d["code"], server={"kind": "table"})

    async def run():
        with pytest.raises(stul.TableError, match="Kód stolu"):
            await p1.join("0000", "dh", thor["id"], sync.snapshot(thor))
        with pytest.raises(stul.TableError, match="jinou hru"):
            await p2.join(state.d["code"], "drd", elwin["id"], sync.snapshot(elwin))
        await _join(p1, thor, state.d["code"], srv)
        assert thor["campaign"]["status"] == "pending"
        await sync.sync_gm(pj, camp)
        assert [m["snapshot"]["name"] for m in sync.players(camp, "pending")] == ["Thorgrim"]
        await pj.set_status(camp["id"], p1.uid, "approved")
        res = await sync.sync_player(p1, thor)
        assert thor["campaign"]["status"] == "approved" and res["notice"]
        model.add_history(thor, "Útok", "11")
        camp["outbox"] += [{"op": "roll", "label": "Past", "result": "4", "hidden": True},
                           {"op": "adjust", "uid": p1.uid, "payload": {"hp_delta": -5, "reason": "zásah"}},
                           {"op": "message", "uid": p1.uid, "body": "Tajné"}]
        await sync.sync_player(p1, thor)
        await sync.sync_gm(pj, camp)
        hp = thor["hp"]
        res = await sync.sync_player(p1, thor)
        assert thor["hp"] == hp - 5 and "Životy" in res["notice"] and thor["campaign"]["messages"][0]["body"] == "Tajné"
        feed = {r["label"]: r["result"] for r in thor["campaign"]["feed"]}
        assert feed["Útok"] == "11" and feed["Skrytý hod"] == "jen pro PJ"
        assert camp["sheets"][p1.uid]["name"] == "Thorgrim"
        with pytest.raises(stul.TableError):
            await p1.share_image(camp["id"], b"x", "hack")
        path = await pj.share_image(camp["id"], b"MAPA", "Mapa")
        await sync.sync_player(p1, thor)
        assert await p1.download_image(path) == b"MAPA"
        # zámek a vyloučení
        await pj.update_campaign(camp["id"], {"locked": True})
        with pytest.raises(stul.TableError, match="zamčená"):
            await p2.join(state.d["code"], "dh", "x", {"name": "Nový"})
        await pj.kick(camp["id"], p1.uid)
        await sync.sync_player(p1, thor)
        assert thor["campaign"]["gone"]
        # stav stolu se dá uložit a znovu načíst
        again = stul.TableState(json.loads(json.dumps(state.dump())))
        assert again.d["code"] == state.d["code"] and again.d["locked"]
    asyncio.run(run())


def test_table_offline(monkeypatch):
    async def down(*a):
        raise OSError("nic")
    monkeypatch.setattr(stul, "TRANSPORT", down)
    c = model.create_character("dh", "Gorm", "Trpaslík", "Válečník", [18, 9, 19, 10, 7])
    srv = {"kind": "table", "host": "10.0.0.9:47821", "code": "1234"}
    c["campaign"] = sync.base_campaign("dh", id="stul-1", name="X", code="1234", role="player", server=srv)
    cl = stul.RemoteTable({}, lambda: None, srv)
    asyncio.run(sync.sync_player(cl, c))
    assert c["campaign"]["online"] is False and "Stůl PJ nenalezen" in c["campaign"]["error"]


def test_table_real_network():
    """Skutečný server stolu na 127.0.0.1: hledání (ping) a dotaz přes HTTP."""
    state = stul.TableState(name="Věž", system="drd")

    async def run():
        host = stul.Host(state)
        assert await host.start(port=0, host="127.0.0.1")
        addr = f"127.0.0.1:{host.port}"
        found = await stul.find_tables(hosts=[addr, "127.0.0.1:1"])
        assert len(found) == 1 and found[0]["name"] == "Věž" and found[0]["host"] == addr
        cl = stul.RemoteTable({}, lambda: None, {"kind": "table", "host": addr, "code": state.d["code"]})
        old = stul.TRANSPORT
        stul.TRANSPORT = None
        try:
            row = await cl.join(state.d["code"], "drd", "c1", {"name": "Elwin"})
        finally:
            stul.TRANSPORT = old
        assert row["name"] == "Věž" and state.d["members"][cl.uid]["status"] == "pending"
        await host.stop()
        assert not host.running
    asyncio.run(run())
