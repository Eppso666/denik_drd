"""Družina a propojení hráčů – kampaň, členové, hody a fronta změn.

Kampaň patří vždy k jedné hře (DrD nebo DH) a postava je v ní jako kopie – originál zůstává v telefonu.
Server (Supabase) se nastaví později: dokud nejsou vyplněné klíče v `config.py`, funguje kampaň jen
v tomto zařízení – PJ ji může založit a dostane kód, hody a změny životů se řadí do fronty
a odešlou se, jakmile bude propojení zapnuté. Připojit se ke kampani někoho jiného jde až se serverem.
"""
from __future__ import annotations

import random
import time

try:  # veřejné údaje projektu Supabase (URL + publishable key)
    from . import config  # type: ignore
except ImportError:  # pragma: no cover
    config = None

# Klient pro Supabase se zapne v další verzi – do té doby kampaň běží jen v tomto zařízení.
CLIENT_READY = False

# Bez 0/O, 1/I/L – kód se dobře přečte i nadiktuje.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


class NotConfigured(Exception):
    """Server pro družinu ještě není nastavený."""


def configured() -> bool:
    has_keys = bool(config and getattr(config, "SUPABASE_URL", "") and getattr(config, "SUPABASE_KEY", ""))
    return CLIENT_READY and has_keys


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


def create_campaign(c: dict, name: str) -> dict:
    """Založí kampaň pro hru této postavy; zakladatel je PJ."""
    camp = {
        "id": f"local-{int(time.time())}-{random.randint(1000, 9999)}",
        "name": name.strip() or "Nová kampaň", "system": c["system"], "code": new_code(), "session": 1,
        "role": "gm", "share_rolls": True, "share_hp": True, "joined": time.time(), "synced": time.time(),
        "images": [], "members": [], "online": False,
    }
    c["campaign"] = camp
    return camp


def join_campaign(c: dict, code: str) -> dict:
    """Připojí postavu ke kampani podle kódu – vyžaduje server."""
    if normalize_code(code) is None:
        raise ValueError("Kód má 6 znaků, např. K7P-42Q.")
    # Bez serveru se kampaň jiného zařízení najít nedá; se Supabase se zde dotáže tabulky campaigns.
    raise NotConfigured()


def leave(c: dict) -> None:
    c.pop("campaign", None)


def can_join(c: dict, camp_system: str) -> bool:
    """Kampaň patří k jedné hře: postava DH se nepřipojí do kampaně DrD a naopak."""
    return c.get("system") == camp_system


def rolls(c: dict) -> list[dict]:
    """Hody postavy od připojení ke kampani (nejnovější první)."""
    camp = campaign(c)
    if not camp:
        return []
    return [h for h in c.get("history", []) if h.get("ts", 0) >= camp["joined"]]


def pending(c: dict) -> int:
    """Kolik změn čeká na odeslání (hody od poslední synchronizace)."""
    camp = campaign(c)
    if not camp:
        return 0
    if not camp.get("share_rolls", True):
        return 0
    return sum(1 for h in c.get("history", []) if h.get("ts", 0) > camp.get("synced", 0))


def snapshot(c: dict) -> dict:
    """Co o postavě uvidí ostatní hráči (batoh a poznámky vidí jen hráč a PJ)."""
    camp = campaign(c) or {}
    return {"name": c["name"], "race": c.get("race"), "cls": c.get("cls"), "level": c.get("level"),
            "hp": c.get("hp") if camp.get("share_hp", True) else None,
            "hp_max": c.get("hp_max") if camp.get("share_hp", True) else None}
