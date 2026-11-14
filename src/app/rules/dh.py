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
    "Klerik": "Mana",
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
