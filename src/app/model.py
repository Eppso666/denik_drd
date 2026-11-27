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
    if system == "drd":
        from .rules import drd_vybava
        c["money"]["zl"] = drd_vybava.START_MONEY_ZL  # PPZ s. 101: dobrodruzi začínají asi s 85 zl
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
        c["fatigue"] = 0
        table = dh.class_mana(cls, 1, attrs)
        if table:
            c["mana_max"] = c["mana"] = table
        if cls == "Alchymista":
            c["raw"] = c["raw_max"] = dh.alch_start_raw(attrs)
        c["xp_next"] = dh.xp_for_level(2)
    else:
        hp = drd.hit_points(cls, attrs)
        c["hp_max"] = c["hp"] = hp
        c["death"] = 0
        c["capacity"] = default_capacity(c)
        c["skill_points"] = 0
        table = drd.class_mana(cls, 1, attrs)
        if table:
            c["mana_max"] = c["mana"] = table
        c["xp_next"] = drd.xp_for_level(cls, 2) or 0
    return c


def uses_mana(c: dict) -> bool:
    """Postava, která kouzlí za magenergii / manu (ukazatel se zobrazí i při nule)."""
    if c.get("system") == "drd":
        return c.get("cls") in drd.MANA_NAME
    return bool(c.get("mana_name"))


def sync_mana(c: dict) -> bool:
    """Starší postavy bez magenergie / many doplní podle tabulky. Vrací True, pokud se něco změnilo."""
    changed = False
    if c.get("system") == "dh" and c.get("cls") == "Klerik" and c.get("mana_name") == "Mana":
        c["mana_name"] = "Přízeň"
        changed = True
    if int(c.get("mana_max", 0)) > 0:
        return changed
    if c.get("system") == "dh":
        table = dh.class_mana(c.get("cls"), c.get("level", 1), c["attrs"])
    else:
        table = drd.class_mana(c.get("cls"), c.get("level", 1), c["attrs"], c.get("branch"))
    if not table:
        return changed
    c["mana_max"] = c["mana"] = table
    c["mana_name"] = c.get("mana_name") or rules(c["system"]).MANA_NAME.get(c["cls"], "Magenergie")
    return True


def xp_next(c: dict) -> int | None:
    """Zkušenost potřebná na další úroveň podle tabulky (None = mimo tabulku)."""
    if c.get("system") == "dh":
        return dh.xp_for_level(int(c["level"]) + 1)
    return drd.xp_for_level(c.get("cls", ""), int(c["level"]) + 1)


def can_level_up(c: dict) -> bool:
    nxt = xp_next(c)
    return bool(nxt) and int(c.get("xp", 0)) >= nxt


def load_ratio(c: dict) -> float:
    return load(c) / max(0.1, float(c.get("capacity", 30)))


def size(c: dict) -> str:
    return (dh.RACE_SIZE if c.get("system") == "dh" else drd.RACE_SIZE).get(c.get("race", ""), "B")


def combat_penalty(c: dict) -> tuple[int, list[str]]:
    """Postih k hodu na útok i obranu: zranění (bojeschopnost) a velké naložení (DrD), únava (DH)."""
    pen, why = 0, []
    if c.get("system") == "drd":
        p = drd.wound_penalty(int(c["hp"]), int(c["hp_max"]), c["attrs"][2])
        if p:
            pen += p
            why.append(f"zranění {p}")
        ratio = load_ratio(c)
        if 3 < ratio:
            pen -= 1
            why.append("velké naložení −1")
    else:
        _, p = dh.fatigue_state(int(c.get("fatigue", 0)), c["attrs"])
        if p:
            pen += p
            why.append(f"únava {p}")
    return pen, why


def status(c: dict) -> tuple[str, str] | None:
    """Stav postavy podle životů: (text, barva) nebo None, když je v pořádku."""
    hp = int(c["hp"])
    if c.get("system") == "dh":
        if hp < int(c.get("death", -10)):
            return "Mrtvá – pod hranicí smrti", "bad"
        if hp <= 0:
            return "V bezvědomí (0 životů a méně)", "bad"
        return None
    if hp <= 0:
        return "V ohrožení života", "bad"
    if drd.is_knocked_out(hp, int(c["hp_max"]), c["attrs"][2]):
        return "Vyřazena z boje", "bad"
    p = drd.wound_penalty(hp, int(c["hp_max"]), c["attrs"][2])
    if p:
        return f"Těžce zraněna – postih {p}", "warn"
    return None


def item(name: str, category: str, qty: int = 1, weight: float = 0.0, equipped: bool = False, **stats) -> dict:
    it = {"id": new_id(), "name": name, "category": category, "qty": qty, "weight": weight, "equipped": equipped}
    it.update(stats)
    return it


def equipped(c: dict, category: str) -> list[dict]:
    return [i for i in c.get("items", []) if i.get("category") == category and i.get("equipped")]


def unarmed(c: dict) -> dict:
    """Beze zbraně. DrD: obrana −3, se samotným štítem 0 (PPZ s. 68 a 72)."""
    dfn = 0
    if c.get("system") == "drd" and not equipped(c, "Štít"):
        dfn = drd_vybava.UNARMED_OZ
    return {"name": "Beze zbraně", "attack": 0, "damage": 0, "defense": dfn, "ranged": False, "unarmed": True}


def weapons(c: dict) -> list[dict]:
    return equipped(c, "Zbraň") or [unarmed(c)]


def is_racial(c: dict, w: dict) -> bool:
    """Rodová zbraň rasy (DrD): +1 k ÚČ."""
    if c.get("system") != "drd":
        return False
    rod = drd_vybava.RODOVE.get(c.get("race", ""))
    return bool(rod) and w.get("name", "").strip().lower() == rod.lower()


def uc(c: dict, w: dict) -> int:
    """Útočné číslo se zbraní (DrD i s bonusem za rodovou zbraň)."""
    return rules(c["system"]).weapon_uc(w, c["attrs"]) + (1 if is_racial(c, w) else 0)


def armor_quality(c: dict) -> int:
    worn = equipped(c, "Zbroj")
    if not worn and c.get("system") == "drd":
        return drd_vybava.NO_ARMOR_KZ  # DrD: bez zbroje je kvalita 1 (Tabulka kvality zbroje)
    return sum(int(i.get("quality", 0)) for i in worn)


def shield_value(c: dict, i: dict) -> int:
    """Bonus štítu k obraně. DrD: vždy +1 (PPZ, Souboj – Obrana); DH: hodnota předmětu."""
    return 1 if c.get("system") == "drd" else int(i.get("defense", 0))


def shield_bonus(c: dict) -> int:
    shields = equipped(c, "Štít")
    if c.get("system") == "drd":
        return 1 if shields else 0  # štít se počítá jednou a vždy +1
    return sum(shield_value(c, i) for i in shields)


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


def shield_for(c: dict, w: dict) -> int:
    """Štít se počítá jen s jednoruční zbraní (obouruční, střelné a dvě zbraně štít nedovolí)."""
    return 0 if int(w.get("hands", 1)) >= 2 else shield_bonus(c)


def oc(c: dict, weapon: dict | None = None) -> int:
    """Obrana celkem pro hod na obranu (DrD: OČ + obrana zbraně + štít; DH: OČ = ZO + zbraň + štít)."""
    w = weapon or weapons(c)[0]
    if c["system"] == "drd":
        return oc_sheet(c) + int(w.get("defense", 0)) + shield_for(c, w)
    return rules(c["system"]).defense_oc(c["attrs"], armor_quality(c), int(w.get("defense", 0)), shield_for(c, w))


def warnings(c: dict) -> list[str]:
    """Upozornění k výbavě: síla na zbraň a zbroj (DH), štít s obouruční zbraní, zbraň mimo povolání."""
    out: list[str] = []
    if c.get("system") == "dh":
        sil = dh.bonus(c["attrs"][0])
        for i in c.get("items", []):
            req = i.get("sil_req")
            if i.get("equipped") and req is not None and sil < int(req):
                out.append(f"{i['name']}: potřebuje Sílu {'+' if req > 0 else ''}{req} (máš {sil:+d}) – "
                           "u činností s * dostaneš navíc body únavy.")
    shields = equipped(c, "Štít")
    if shields and any(int(w.get("hands", 1)) >= 2 for w in equipped(c, "Zbraň")):
        out.append("Se zbraní do obou rukou nelze používat štít – k obraně s ní se nepočítá.")
    if c.get("system") == "drd":
        for i in c.get("items", []):
            if i.get("equipped"):
                note = drd_vybava.gear_problem(c.get("cls", ""), i)
                if note:
                    out.append(note)
    return out


def oc_sheet(c: dict) -> int:
    """DrD: obranné číslo do deníku = kvalita zbroje + oprava OBR, nejméně 0 (PPZ s. 72)."""
    return max(0, drd.bonus(c["attrs"][1]) + armor_quality(c))
