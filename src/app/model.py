"""Datový model postavy a tvorba nové postavy pro obě hry."""
from __future__ import annotations

import time
import uuid

from .rules import dh, dh_vybava, drd, drd_kouzla, drd_vybava


def rules(system: str):
    return dh if system == "dh" else drd


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def create_character(system: str, name: str, race: str, cls: str, attrs: list[int]) -> dict:
    r = rules(system)
    c: dict = {
        "id": new_id(),
        "system": system,
        "name": name.strip() or "Bezejmenný dobrodruh",
        "race": race,
        "cls": cls,
        "level": 1,
        "xp": 0,
        "xp_next": 0,
        "attrs": list(attrs),
        "mana": 0,
        "mana_max": 0,
        "mana_name": r.MANA_NAME.get(cls, "Mana") or "",
        "money": {"zl": 0, "st": 0, "md": 0},
        "items": [],
        "skills": [],
        "abilities": [],
        "load_manual": False,
        "load_value": 0.0,
        "capacity": 30.0,
        "notes": [],
        "images": [],
        "history": [],
        "branch": None,
        "spells": [],
        "companions": [],
        "avatar": None,
        "created": time.time(),
    }
    if system == "dh":
        hp = dh.hit_points(attrs)
        c["hp_max"] = c["hp"] = hp
        c["death"] = dh.death_threshold(attrs)
        c["money"]["zl"] = dh.start_money()
        weapon, armor = dh.START_GEAR[cls]
        wname, att, dmg, wdef, ranged = weapon
        c["items"].append(item(wname, "Zbraň", equipped=True, attack=att, damage=dmg, defense=wdef, ranged=ranged, weight=2))
        if armor:
            c["items"].append(item(armor[0], "Zbroj", equipped=True, quality=armor[1], weight=6))
        for sname, lvl in dh.START_SKILLS[cls]:
            c["skills"].append({"name": sname, "attr": dh.SKILLS.get(sname, "OBR"), "level": lvl, "kind": "Blízká" if lvl == 3 else "Obecná"})
        if race == "Člověk":
            c["skill_points"] = 2  # rodová schopnost Všestrannost
        else:
            c["skill_points"] = 0
        c["capacity"] = float(dh_vybava.carry_capacity(dh.bonus(attrs[0])))
    else:
        hp = drd.hit_points(cls, attrs)
        c["hp_max"] = c["hp"] = hp
        c["death"] = 0
        c["capacity"] = default_capacity(c)
        c["skill_points"] = 0
        if cls == "Kouzelník":
            c["mana_max"] = c["mana"] = drd_kouzla.wizard_mana(1, attrs[3])
    return c


def item(name: str, category: str, qty: int = 1, weight: float = 0.0, equipped: bool = False, **stats) -> dict:
    it = {"id": new_id(), "name": name, "category": category, "qty": qty, "weight": weight, "equipped": equipped}
    it.update(stats)
    return it


def equipped(c: dict, category: str) -> list[dict]:
    return [i for i in c.get("items", []) if i.get("category") == category and i.get("equipped")]


def weapons(c: dict) -> list[dict]:
    ws = equipped(c, "Zbraň")
    return ws or [{"name": "Beze zbraně", "attack": 0, "damage": 0, "defense": 0, "ranged": False}]


def armor_quality(c: dict) -> int:
    worn = equipped(c, "Zbroj")
    if not worn and c.get("system") == "drd":
        return drd_vybava.NO_ARMOR_KZ  # DrD: bez zbroje je kvalita 1 (Tabulka kvality zbroje)
    return sum(int(i.get("quality", 0)) for i in worn)


def shield_bonus(c: dict) -> int:
    return sum(int(i.get("defense", 1 if c["system"] == "drd" else 0)) for i in equipped(c, "Štít"))


def items_weight(c: dict) -> float:
    return round(sum(float(i.get("weight", 0)) * int(i.get("qty", 1)) for i in c.get("items", [])), 1)


def load(c: dict) -> float:
    return float(c["load_value"]) if c.get("load_manual") else items_weight(c)


def default_capacity(c: dict) -> float:
    """Nosnost podle pravidel (DrD: Tabulka nosnosti v mincích → kg; DH: Tabulka nosnosti v librách)."""
    if c.get("system") == "dh":
        return float(dh_vybava.carry_capacity(dh.bonus(c["attrs"][0])))
    return drd_vybava.kg(drd_vybava.carry_capacity_mn(drd.bonus(c["attrs"][0])))


def load_state(c: dict) -> tuple[str, str]:
    """Vrací (popis, klíč barvy). Naložení podle násobků nosnosti (do 4× nosnosti)."""
    cap = max(0.1, float(c.get("capacity", 30)))
    ratio = load(c) / cap
    is_dh = c.get("system") == "dh"
    if ratio <= 1:
        return "Bez naložení", "ok"
    if ratio <= 2:
        return ("Pohyblivost −¼" if is_dh else "Mírné naložení · pohyblivost ¾"), "warn"
    if ratio <= 3:
        return ("Pohyblivost −½" if is_dh else "Střední naložení · pohyblivost ½"), "warn"
    if ratio <= 4:
        return ("Pohyblivost −¾" if is_dh else "Velké naložení · pohyblivost ¼, útok −1"), "bad"
    return "Přetížen – nad 4× nosnost", "bad"


def add_history(c: dict, label: str, value: str) -> None:
    c.setdefault("history", []).insert(0, {"label": label, "value": value, "ts": time.time()})
    del c["history"][30:]


def oc(c: dict, weapon: dict | None = None) -> int:
    r = rules(c["system"])
    w = weapon or weapons(c)[0]
    return r.defense_oc(c["attrs"], armor_quality(c), int(w.get("defense", 0)), shield_bonus(c))
