"""Klient Družiny proti falešnému serveru Supabase (v paměti)."""
import asyncio
import json
import re
import time
import urllib.parse as up

from app import model, sync


class FakeSupabase:
    """Zjednodušený Supabase: anonymní přihlášení, RPC, tabulky a úložiště – s pravidly jako v schema.sql."""

    def __init__(self):
        self.users = {}
        self.campaigns = []
        self.members = []
        self.sheets = []
        self.rolls = []
        self.images = []
        self.files = {}
        self.n = 0
        self.anonymous = True

    def _uid(self, headers):
        tok = headers.get("Authorization", "").removeprefix("Bearer ")
        return self.users.get(tok)

    def _member(self, cid, uid):
        return next((m for m in self.members if m["campaign_id"] == cid and m["user_id"] == uid), None)

    async def __call__(self, method, url, headers, body):
        u = up.urlparse(url)
        path, q = u.path, dict(up.parse_qsl(u.query))
        data = json.loads(body) if body and headers.get("Content-Type") == "application/json" else body
        if path == "/auth/v1/signup":
            if not self.anonymous:
                return 422, b'{"msg":"Anonymous sign-ins are disabled"}'
            self.n += 1
            uid, tok = f"user-{self.n}", f"tok-{self.n}"
            self.users[tok] = uid
            return 200, json.dumps({"access_token": tok, "refresh_token": "r" + tok, "expires_in": 3600,
                                    "user": {"id": uid}}).encode()
        uid = self._uid(headers)
        if uid is None:
            return 401, b'{"message":"JWT expired"}'
        eq = {k: v.removeprefix("eq.") for k, v in q.items() if v.startswith("eq.")}
        if path == "/rest/v1/rpc/create_campaign":
            self.n += 1
            camp = {"id": f"camp-{self.n}", "name": data["p_name"], "system": data["p_system"],
                    "code": sync.new_code(), "session": 1, "gm": uid}
            self.campaigns.append(camp)
            self.members.append({"campaign_id": camp["id"], "user_id": uid, "role": "gm",
                                 "snapshot": data["p_snapshot"], "last_seen": time.time(), "share_hp": True})
            return 200, json.dumps(camp).encode()
        if path == "/rest/v1/rpc/join_campaign":
            camp = next((c for c in self.campaigns if c["code"] == data["p_code"]), None)
            if not camp:
                return 400, json.dumps({"message": "Kampaň s tímto kódem neexistuje."}).encode()
            if camp["system"] != data["p_system"]:
                return 400, json.dumps({"message": "Kampaň je pro jinou hru."}).encode()
            if not self._member(camp["id"], uid):
                self.members.append({"campaign_id": camp["id"], "user_id": uid, "role": "player",
                                     "snapshot": data["p_snapshot"], "last_seen": time.time(), "share_hp": True})
            return 200, json.dumps(camp).encode()
        table = path.removeprefix("/rest/v1/")
        if path.startswith("/storage/v1/object/"):
            p = re.sub(r"^/storage/v1/object/(authenticated/)?campaign-images/", "", path)
            cid = p.split("/")[0]
            m = self._member(cid, uid)
            if method == "POST":
                if not m or m["role"] != "gm":
                    return 403, b'{"message":"forbidden"}'
                self.files[p] = body
                return 200, b"{}"
            return (200, self.files[p]) if m and p in self.files else (404, b"")
        cid = eq.get("campaign_id") or eq.get("id")
        if table == "campaigns":
            rows = [c for c in self.campaigns if c["id"] == cid and self._member(c["id"], uid)]
            if method == "GET":
                return 200, json.dumps(rows).encode()
            if method == "PATCH":
                for c in rows:
                    if c["gm"] == uid:
                        c.update(data)
                return 204, b""
            if method == "DELETE":
                for c in rows:
                    if c["gm"] == uid:
                        self.campaigns.remove(c)
                        self.members = [m for m in self.members if m["campaign_id"] != c["id"]]
                return 204, b""
        if table == "members":
            if method == "GET":
                rows = [m for m in self.members if m["campaign_id"] == cid and self._member(cid, uid)]
                return 200, json.dumps(rows, default=str).encode()
            if method == "PATCH":
                m = self._member(cid, eq["user_id"])
                if m and eq["user_id"] == uid:
                    m.update(data)
                return 204, b""
            if method == "DELETE":
                self.members = [m for m in self.members if not (m["campaign_id"] == cid and m["user_id"] == uid)]
                return 204, b""
        if table == "member_sheets":
            if method == "POST":
                self.sheets = [s for s in self.sheets if not (s["campaign_id"] == data["campaign_id"]
                                                              and s["user_id"] == uid)]
                self.sheets.append(dict(data, user_id=uid))
                return 201, b""
            gm = (self._member(cid, uid) or {}).get("role") == "gm"
            rows = [s for s in self.sheets if s["campaign_id"] == cid and s["user_id"] == eq["user_id"]
                    and (gm or s["user_id"] == uid)]
            return 200, json.dumps(rows).encode()
        if table == "rolls":
            for r in data:
                m = self._member(r["campaign_id"], uid)
                if not m or (r["hidden"] and m["role"] != "gm"):
                    return 403, b'{"message":"rls"}'
                self.rolls.append(dict(r, user_id=uid, created_at=time.time()))
            return 201, b""
        if table == "rolls_feed":
            gm = (self._member(cid, uid) or {}).get("role") == "gm"
            rows = []
            for r in reversed(self.rolls):
                if r["campaign_id"] != cid or not self._member(cid, uid):
                    continue
                masked = r["hidden"] and r["user_id"] != uid and not gm
                rows.append({"who": r["who"], "label": "Skrytý hod" if masked else r["label"],
                             "result": "jen pro PJ" if masked else r["result"], "hidden": r["hidden"],
                             "created_at": r["created_at"]})
            return 200, json.dumps(rows).encode()
        if table == "shared_images":
            if method == "POST":
                self.images.append(dict(data, id=len(self.images) + 1, created_at=time.time()))
                return 201, b""
            rows = [i for i in self.images if i["campaign_id"] == cid and self._member(cid, uid)]
            return 200, json.dumps(rows).encode()
        return 404, b'{"message":"unknown"}'


def _client(settings):
    return sync.Client(settings, lambda: None)


def test_campaign_flow(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    gm_c = model.create_character("drd", "Petra", "Člověk", "Válečník", [12, 12, 12, 12, 12])
    pl_c = model.create_character("drd", "Elwin", "Elf", "Hraničář", [10, 14, 11, 13, 12])
    dh_c = model.create_character("dh", "Gorm", "Trpaslík", "Válečník", [18, 9, 19, 10, 7])
    gm, pl, other = _client({}), _client({}), _client({})

    async def scenario():
        camp = await gm.create(gm_c, "Prokletí Černé věže")
        assert camp["role"] == "gm" and camp["online"] and len(camp["members"]) == 1
        # postava jiné hry se nepřipojí
        try:
            await other.join(dh_c, camp["code"])
            raise AssertionError
        except sync.SyncError as ex:
            assert "jinou hru" in str(ex)
        await pl.join(pl_c, camp["code"].lower().replace("-", " "))
        assert pl_c["campaign"]["role"] == "player"
        # hráč hodí, PJ hodí skrytě
        model.add_history(pl_c, "Útok", "16")
        await pl.sync(pl_c)
        gm_c["campaign"]["hide_rolls"] = True
        model.add_history(gm_c, "Past", "5")
        await gm.sync(gm_c)
        await pl.sync(pl_c)
        feed = {r["label"]: r["result"] for r in pl_c["campaign"]["feed"]}
        assert feed["Útok"] == "16" and feed["Skrytý hod"] == "jen pro PJ"
        assert sync.pending(pl_c) == 0
        # členové a životy
        assert len(pl_c["campaign"]["members"]) == 2
        pl_c["hp"] = 3
        pl_c["campaign"]["share_hp"] = True
        await pl.sync(pl_c)
        await gm.sync(gm_c)
        snap = {m["snapshot"]["name"]: m["snapshot"] for m in gm_c["campaign"]["members"]}
        assert snap["Elwin"]["hp"] == 3
        # PJ vidí deník hráče, hráč deník PJ ne
        assert (await gm.member_sheet(gm_c["campaign"], pl.uid))["name"] == "Elwin"
        assert await pl.member_sheet(pl_c["campaign"], gm.uid) is None
        # sezení a obrázek
        await gm.set_session(gm_c, 2)
        await gm.share_image(gm_c, b"JPEGDATA", "Mapa")
        await pl.sync(pl_c)
        assert pl_c["campaign"]["session"] == 2 and pl_c["campaign"]["images"][0]["title"] == "Mapa"
        assert await pl.download_image(pl_c["campaign"]["images"][0]["path"]) == b"JPEGDATA"
        try:
            await pl.share_image(pl_c, b"x", "hack")
            raise AssertionError
        except sync.SyncError:
            pass
        # hráč odejde, PJ ukončí kampaň
        await pl.leave(pl_c)
        assert "campaign" not in pl_c and len(srv.members) == 1
        await gm.leave(gm_c)
        assert not srv.campaigns

    asyncio.run(scenario())


def test_offline_and_errors(monkeypatch):
    c = model.create_character("drd", "Elwin", "Elf", "Hraničář", [10, 14, 11, 13, 12])
    srv = FakeSupabase()
    srv.anonymous = False
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    cl = _client({})

    async def go():
        try:
            await cl.create(c, "X")
            raise AssertionError
        except sync.SyncError as ex:
            assert "anonymní" in str(ex)
    asyncio.run(go())
    # výpadek sítě: kampaň zůstane, hody čekají
    srv.anonymous = True
    asyncio.run(cl.create(c, "Doly"))

    async def offline(*a):
        raise OSError("bez sítě")
    monkeypatch.setattr(sync, "TRANSPORT", offline)
    model.add_history(c, "Útok", "9")
    asyncio.run(cl.sync(c))
    assert c["campaign"]["online"] is False and sync.pending(c) == 1
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    asyncio.run(cl.sync(c))
    assert c["campaign"]["online"] and sync.pending(c) == 0 and srv.rolls[0]["result"] == "9"


def test_auth_refresh(monkeypatch):
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    settings = {}
    cl = _client(settings)
    asyncio.run(cl.ensure_auth())
    uid = cl.uid
    settings["sb_auth"]["exp"] = 0  # vypršelo → refresh selže ve fake serveru → nový účet, ale nespadne
    asyncio.run(cl.ensure_auth())
    assert cl.uid and settings["sb_auth"]["exp"] > time.time()
    assert uid


def test_druzina_screen_online(make_app, monkeypatch):
    from test_ui import click_everything, drain, walk
    srv = FakeSupabase()
    monkeypatch.setattr(sync, "TRANSPORT", srv)
    app, page = make_app()
    c = model.create_character("dh", "Thorgrim", "Trpaslík", "Válečník", [18, 9, 19, 10, 7])
    app.add_character(c)
    app.open_character(c["id"])
    drain(page)
    asyncio.run(app.sync.create(c, "Doly pod Černou horou"))
    other = model.create_character("dh", "Mirka", "Elf", "Hraničář", [10, 14, 11, 13, 12])
    asyncio.run(_client({}).join(other, c["campaign"]["code"]))
    asyncio.run(app.sync.sync(c))
    app.go("druzina")
    drain(page)
    texts = [str(getattr(x, "value", "")) for v in page.views for x in walk(v)]
    assert "Doly pod Černou horou" in texts and "Mirka" in texts and any("Propojeno" in t for t in texts)
    assert click_everything(app, page) > 0
