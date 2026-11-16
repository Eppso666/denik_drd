"""Pravidla Dračí Hlídky (Příručka pro hráče, 2021).

Tabulky jsou převzaté z kapitol Tvorba postavy, Herní mechaniky a Dovednosti.
Kostky: k10 pro ověřovací hody a pasti, k6 pro boj.
"""
from __future__ import annotations

import random

from .common import d, open_d6

SYSTEM = "dh"
NAME = "Dračí Hlídka"
SHORT = "DH"
DICE = ["k6", "k6+", "k10"]

ATTRS = ["SIL", "OBR", "ODO", "INT", "CHAR"]
ATTR_NAMES = ["Síla", "Obratnost", "Odolnost", "Inteligence", "Charisma"]

# Tabulka rodových atributů
RACES: dict[str, list[int]] = {
    "Člověk": [7, 7, 7, 7, 7],
    "Trpaslík": [10, 5, 10, 5, 5],
    "Elf": [6, 7, 5, 10, 9],
    "Barbar": [9, 8, 8, 5, 5],
    "Obr": [12, 3, 10, 3, 3],
    "Gnóm": [4, 10, 5, 9, 5],
    "Půlčík": [6, 9, 6, 7, 8],
}

# Dominantní vlastnosti povolání (+3)
CLASSES: dict[str, tuple[str, str]] = {
    "Válečník": ("SIL", "ODO"),
    "Hraničář": ("OBR", "INT"),
    "Alchymista": ("OBR", "ODO"),
    "Kouzelník": ("INT", "CHAR"),
    "Zloděj": ("OBR", "CHAR"),
    "Klerik": ("INT", "CHAR"),
}

MANA_NAME = {
    "Válečník": "Adrenalin",
    "Hraničář": "Duševní síla",
    "Alchymista": "Mana",
    "Kouzelník": "Mana",
    "Zloděj": "",
    "Klerik": "Přízeň",
}

# Zbraně a zbroje dle povolání: (název, útočnost, zranění, obrana, střelná), zbroj (název, kvalita)
START_GEAR: dict[str, tuple[tuple[str, int, int, int, bool], tuple[str, int] | None]] = {
    "Válečník": (("Krátký meč", 4, 1, 2, False), ("Prošívaná zbroj", 2)),
    "Hraničář": (("Krátký luk", 4, 0, 0, True), None),
    "Alchymista": (("Lehká kuše", 4, 1, 1, True), None),
    "Kouzelník": (("Dřevěná hůl", 5, 0, 1, False), None),
    "Zloděj": (("Lehká kuše", 4, 1, 1, True), None),
    "Klerik": (("Dřevěná hůl", 5, 0, 1, False), None),
}

# Tabulka základních dovedností: název -> výchozí vlastnost
SKILLS: dict[str, str] = {
    "Akrobacie": "OBR",
    "Atletika": "SIL",
    "Cizí jazyky": "INT",
    "Čtení a psaní": "INT",
    "Historie": "INT",
    "Jízda na zvířeti": "OBR",
    "Mechanika": "INT",
    "Plavání": "SIL",
    "Plížení": "OBR",
    "Postřeh": "INT",
    "První pomoc": "OBR",
    "Přežití v přírodě": "OBR",
    "Reflex": "OBR",
    "Řemesla": "OBR",
    "Umění": "CHAR",
    "Teologie": "INT",
    "Vůle": "CHAR",
    "Výdrž": "ODO",
    "Znalost přírody": "INT",
    "Zpracování zvěře": "OBR",
}

# Doporučené dovednosti pro začínající hráče (3 blízké na 3. stupni + 3 volitelné na 1.)
START_SKILLS: dict[str, list[tuple[str, int]]] = {
    "Válečník": [("Atletika", 3), ("První pomoc", 3), ("Výdrž", 3), ("Plavání", 1), ("Jízda na zvířeti", 1), ("Přežití v přírodě", 1)],
    "Hraničář": [("Přežití v přírodě", 3), ("První pomoc", 3), ("Znalost přírody", 3), ("Jízda na zvířeti", 1), ("Plavání", 1), ("Zpracování zvěře", 1)],
    "Alchymista": [("Znalost přírody", 3), ("Mechanika", 3), ("Čtení a psaní", 3), ("Reflex", 1), ("Postřeh", 1), ("Zpracování zvěře", 1)],
    "Kouzelník": [("Čtení a psaní", 3), ("Historie", 3), ("Cizí jazyky", 3), ("Vůle", 1), ("Postřeh", 1), ("Teologie", 1)],
    "Zloděj": [("Akrobacie", 3), ("Postřeh", 3), ("Reflex", 3), ("Umění", 1), ("Plížení", 1), ("Čtení a psaní", 1)],
    "Klerik": [("Čtení a psaní", 3), ("Teologie", 3), ("Vůle", 3), ("První pomoc", 1), ("Cizí jazyky", 1), ("Historie", 1)],
}

ADVANTAGE = 5  # Výhoda +5 / Nevýhoda −5


def bonus(value: int) -> int:
    """Tabulka oprav za atribut: 1 – −5, 2–3 – −4, …, 10–11 – 0, 12–13 – +1, … (+1 za každé 2 stupně)."""
    return value // 2 - 5


def generate_auto(race: str, cls: str, rng: random.Random | None = None) -> list[int]:
    """6× k6, nejnižší se škrtne, zbylých 5 se rozdělí (nejvyšší do dominantních), + rodový základ + 3 k dominantním."""
    rolls = sorted((d(6, rng) for _ in range(6)), reverse=True)[:5]
    dom = CLASSES[cls]
    order = [a for a in ATTRS if a in dom] + [a for a in ATTRS if a not in dom]
    assigned = dict(zip(order, rolls))
    return finalize([assigned[a] for a in ATTRS], race, cls)


def finalize(points: list[int], race: str, cls: str) -> list[int]:
    """Body z hodu (nebo rozdělení) + rodový základ + 3 k dominantním vlastnostem."""
    base = RACES[race]
    dom = CLASSES[cls]
    return [p + b + (3 if ATTRS[i] in dom else 0) for i, (p, b) in enumerate(zip(points, base))]


POINT_POOL = 20  # alternativní tvorba: 20 bodů, do každé vlastnosti 1–6
POINT_MIN, POINT_MAX = 1, 6


def hit_points(attrs: list[int]) -> int:
    """Životy = 10 + oprava ODO."""
    return 10 + bonus(attrs[2])


def death_threshold(attrs: list[int]) -> int:
    """Hranice smrti = −(10 + ODO)."""
    return -(10 + bonus(attrs[2]))


def start_money(rng: random.Random | None = None) -> int:
    """Zlaťáky na začátku hry: 1k10 + 30."""
    return d(10, rng) + 30


def check(attr_bonus: int, level: int, difficulty: int, adv: int = 0, rng: random.Random | None = None):
    """Ověřovací hod: 1k10 + oprava + stupeň (+ výhoda ±5). Úspěch, pokud výsledek PŘEKONÁ obtížnost."""
    k = d(10, rng)
    total = k + attr_bonus + level + adv * ADVANTAGE
    return k, total, total > difficulty


def initiative(obr_bonus: int, rng: random.Random | None = None) -> tuple[int, int]:
    k = d(6, rng)
    return k, k + obr_bonus


def weapon_uc(weapon: dict, attrs: list[int]) -> int:
    """ÚČ = útočnost zbraně + SIL (boj tváří v tvář) / + OBR (střelecký souboj)."""
    idx = 1 if weapon.get("ranged") else 0
    return int(weapon.get("attack", 0)) + bonus(attrs[idx])


def base_defense(attrs: list[int], armor_quality: int) -> int:
    """ZO = OBR + kvalita zbroje."""
    return bonus(attrs[1]) + armor_quality


def defense_oc(attrs: list[int], armor_quality: int, weapon_def: int, shield: int) -> int:
    """OČ = ZO + obrana zbraně + štít (boj tváří v tvář)."""
    return base_defense(attrs, armor_quality) + weapon_def + shield


def ranged_defense(attrs: list[int], armor_quality: int, shield: int) -> int:
    """Obrana proti střelbě = ZO + štít."""
    return base_defense(attrs, armor_quality) + shield


def wound(attack_total: int, defense_total: int, weapon_damage: int) -> int:
    """Zásah, pokud útok > obrana. Zranění = rozdíl + zranění zbraně (nejméně 1).

    Pozn.: přesné znění kapitoly „Boj a jeho pravidla“ ověř v příručce; vzorec ÚČ/OČ je z osobního deníku DH.
    """
    if attack_total <= defense_total:
        return 0
    return max(1, attack_total - defense_total + weapon_damage)


def combat_roll(exploding: bool, rng: random.Random | None = None) -> list[int]:
    return open_d6(rng) if exploding else [d(6, rng)]


# --- rozvoj postavy (kapitola Rozvoj postavy) --------------------------------------------------

# Tabulka dovednostních bodů: násobek úrovně za přestup
SKILL_POINTS = {"Válečník": 3, "Hraničář": 5, "Alchymista": 4, "Kouzelník": 3, "Zloděj": 8, "Klerik": 3}

# Tabulka zkušeností: úroveň 1–24
XP_TABLE = [0, 550, 1100, 2200, 4400, 8500, 15000, 24000, 36000, 51000, 69000, 90000, 114000, 141000, 170000,
            200000, 230000, 260000, 290000, 320000, 350000, 380000, 410000, 440000]
MAX_LEVEL = 24
ATTR_UP_EVERY = 3  # na každé třetí úrovni 2 charakterové body do dvou různých atributů


def xp_for_level(level: int) -> int | None:
    return XP_TABLE[int(level) - 1] if 1 <= int(level) <= MAX_LEVEL else None


def level_for_xp(xp: int) -> int:
    return max(i + 1 for i, v in enumerate(XP_TABLE) if xp >= v)


def attr_up_level(level: int) -> bool:
    return int(level) % ATTR_UP_EVERY == 0


def level_hp_roll(attrs: list[int], fixed: bool = False, rng: random.Random | None = None) -> tuple[int, int]:
    """Přírůstek životů = 1k6 + ODO (nebo pevně 3 + ODO), vždy alespoň 1."""
    k = 3 if fixed else d(6, rng)
    return k, max(1, k + bonus(attrs[2]))


# Duševní síla hraničáře (INT), mana kouzelníka (INT), přízeň klerika (CHAR): úroveň 1–6, sloupce stupeň 4–23
_COLS0 = 4
RANGER_POWER = {
    1: [4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13],
    2: [5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15],
    3: [7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16],
    4: [8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18],
    5: [10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19],
    6: [11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21],
}
WIZARD_MANA = {
    1: [2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12],
    2: [3, 4, 5, 5, 6, 7, 8, 8, 9, 10, 11, 11, 12, 13, 14, 14, 15, 16, 17, 17],
    3: [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    4: [5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 18, 19, 20, 21, 23, 24, 25, 26, 28, 29],
    5: [6, 8, 9, 11, 12, 14, 15, 17, 18, 20, 21, 23, 24, 26, 27, 29, 30, 32, 33, 35],
    6: [7, 9, 11, 12, 14, 16, 18, 19, 21, 23, 25, 26, 28, 30, 32, 33, 35, 37, 39, 40],
}
CLERIC_FAVOR = {
    1: [5, 6, 6, 7, 7, 7, 8, 8, 9, 9, 9, 10, 10, 11, 11, 11, 12, 12, 13, 13],
    2: [7, 8, 8, 9, 10, 10, 11, 11, 12, 13, 13, 14, 14, 15, 16, 16, 17, 17, 18, 19],
    3: [9, 10, 10, 11, 12, 13, 14, 14, 15, 16, 17, 18, 18, 19, 20, 21, 22, 22, 23, 24],
    4: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29],
    5: [12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 27, 28, 29, 30, 31, 33, 34, 35],
    6: [14, 15, 17, 18, 19, 21, 22, 24, 25, 26, 28, 29, 31, 32, 33, 35, 36, 38, 39, 41],
}
# Alchymista: mana a suroviny na začátku hry podle stupně OBR 4–21
ALCH_START_MANA = [20, 30, 40, 50, 60, 70, 75, 80, 90, 95, 100, 110, 120, 130, 145, 160, 180, 200]
ALCH_START_RAW = [90, 110, 125, 140, 155, 165, 175, 180, 185, 190, 200, 210, 220, 230, 240, 250, 260, 270]


def class_mana(cls: str, level: int, attrs: list[int]) -> int | None:
    """Mana / duševní síla / přízeň podle tabulek (úroveň 1–6; výše hodnota 6. úrovně). None = podle příručky ručně."""
    lvl = max(1, min(6, int(level)))
    if cls == "Hraničář":
        table, val = RANGER_POWER, attrs[3]
    elif cls == "Kouzelník":
        table, val = WIZARD_MANA, attrs[3]
    elif cls == "Klerik":
        table, val = CLERIC_FAVOR, attrs[4]
    elif cls == "Alchymista" and int(level) == 1:
        return ALCH_START_MANA[max(0, min(len(ALCH_START_MANA) - 1, attrs[1] - 4))]
    else:
        return None
    if val < _COLS0:
        return 0
    return table[lvl][min(len(table[lvl]) - 1, val - _COLS0)]


def alch_start_raw(attrs: list[int]) -> int:
    return ALCH_START_RAW[max(0, min(len(ALCH_START_RAW) - 1, attrs[1] - 4))]


# Únava (kapitola Užitečné informace): hranice únavy = 10 + ODO
def fatigue_limit(attrs: list[int]) -> int:
    return 10 + bonus(attrs[2])


def fatigue_state(points: int, attrs: list[int]) -> tuple[str, int]:
    lim = fatigue_limit(attrs)
    if points > 2 * lim:
        return "Zcela vyčerpaný", -6
    if points > lim:
        return "Unavený", -3
    return "Svěží", 0


# Pohyblivost dle rasy (+ OBR); naložení ji snižuje o čtvrtinu za každý násobek nosnosti
RACE_MOVE = {"Barbar": 30, "Trpaslík": 20, "Člověk": 30, "Půlčík": 20, "Elf": 30, "Gnóm": 20, "Obr": 40}
RACE_SIZE = {"Člověk": "B", "Trpaslík": "A", "Elf": "B", "Barbar": "B", "Obr": "C", "Gnóm": "A", "Půlčík": "A"}


def movement(race: str, attrs: list[int], load_ratio: float = 0) -> int:
    import math
    base = RACE_MOVE.get(race, 30) + bonus(attrs[1])
    over = max(0, math.ceil(load_ratio) - 1) if load_ratio > 1 else 0
    return max(0, math.ceil(base * max(0.0, 1 - 0.25 * over)))
