"""Pravidla Dračího doupěte 1.6 (Pravidla pro začátečníky, ALTAR).

Tabulky z kapitol Tvoje postava, Pravidla pro boj a …a mimo boj.
Kostky: k6, k6+ (boj), k10 (pasti), k% (schopnosti).
"""
from __future__ import annotations

import random

from .common import d, open_d6

SYSTEM = "drd"
NAME = "Dračí doupě 1.6"
SHORT = "DrD 1.6"
DICE = ["k6", "k6+", "k10", "k%"]

ATTRS = ["SIL", "OBR", "ODL", "INT", "CHA"]
ATTR_NAMES = ["Síla", "Obratnost", "Odolnost", "Inteligence", "Charisma"]

# Tabulka vlastností podle rasy (rozsahy pro vlastnosti, které nejsou základní pro povolání)
RACE_RANGES: dict[str, list[tuple[int, int]]] = {
    "Hobit": [(3, 8), (11, 16), (8, 13), (10, 15), (8, 18)],
    "Kudůk": [(5, 10), (10, 15), (10, 15), (9, 14), (7, 12)],
    "Trpaslík": [(7, 12), (7, 12), (12, 17), (8, 13), (7, 12)],
    "Elf": [(6, 11), (10, 15), (6, 11), (12, 17), (8, 18)],
    "Člověk": [(6, 16), (9, 14), (9, 14), (10, 15), (2, 17)],
    "Barbar": [(10, 15), (8, 13), (11, 16), (6, 11), (1, 16)],
    "Kroll": [(11, 16), (5, 10), (13, 18), (2, 7), (1, 11)],
}

# Tabulka oprav (posun rozsahu základních vlastností povolání podle rasy)
RACE_MODS: dict[str, list[int]] = {
    "Hobit": [-5, 2, 0, -2, 3],
    "Kudůk": [-3, 1, 1, -2, 0],
    "Trpaslík": [1, -2, 3, -3, -2],
    "Elf": [0, 1, -4, 2, 2],
    "Člověk": [0, 0, 0, 0, 0],
    "Barbar": [1, -1, 1, 0, -2],
    "Kroll": [3, -4, 3, -6, -5],
}

# Tabulka vlastností podle povolání (základní vlastnosti, rozsahy pro člověka)
CLASS_RANGES: dict[str, dict[str, tuple[int, int]]] = {
    "Válečník": {"SIL": (13, 18), "ODL": (13, 18)},
    "Hraničář": {"SIL": (11, 16), "INT": (12, 17)},
    "Alchymista": {"OBR": (13, 18), "ODL": (12, 17)},
    "Kouzelník": {"INT": (14, 19), "CHA": (13, 18)},
    "Zloděj": {"OBR": (14, 19), "CHA": (12, 17)},
}
CLASSES = list(CLASS_RANGES)

# Tabulka životů: základ na 1. úrovni, kostka (stěny, přičtené číslo) při postupu
HP_TABLE: dict[str, tuple[int, int, int]] = {
    "Válečník": (10, 10, 0),
    "Hraničář": (8, 6, 2),
    "Alchymista": (7, 6, 1),
    "Kouzelník": (6, 6, 0),
    "Zloděj": (6, 6, 0),
}

MANA_NAME = {"Hraničář": "Magenergie", "Kouzelník": "Magenergie", "Alchymista": "Magenergie"}


def bonus(value: int) -> int:
    """Tabulka postihů a bonusů."""
    table = [(1, -5), (3, -4), (5, -3), (7, -2), (9, -1), (12, 0), (14, 1), (16, 2), (18, 3), (20, 4)]
    for top, b in table:
        if value <= top:
            return b
    return 5 + (value - 21) // 2


def range_dice(lo: int, hi: int) -> tuple[int, int]:
    """Rozsah – (počet k6, přičtené číslo): rozpětí 5 = 1k6, 10 = 2k6, 15 = 3k6."""
    n = max(1, (hi - lo) // 5)
    return n, lo - n


def roll_range(lo: int, hi: int, rng: random.Random | None = None) -> int:
    n, add = range_dice(lo, hi)
    return sum(d(6, rng) for _ in range(n)) + add


def attr_range(race: str, cls: str, idx: int) -> tuple[int, int]:
    """Rozsah vlastnosti pro danou rasu a povolání."""
    a = ATTRS[idx]
    if a in CLASS_RANGES[cls]:
        lo, hi = CLASS_RANGES[cls][a]
        m = RACE_MODS[race][idx]
        return lo + m, hi + m
    return RACE_RANGES[race][idx]


def generate_auto(race: str, cls: str, rng: random.Random | None = None) -> list[int]:
    return [roll_range(*attr_range(race, cls, i), rng) for i in range(5)]


def hit_points(cls: str, attrs: list[int]) -> int:
    """Životy na 1. úrovni = základ povolání + oprava ODL."""
    return max(1, HP_TABLE[cls][0] + bonus(attrs[2]))


def level_hp_roll(cls: str, attrs: list[int], rng: random.Random | None = None) -> tuple[int, int]:
    """Přírůstek životů při postupu: kostka povolání + oprava ODL, vždy alespoň 1."""
    _, sides, add = HP_TABLE[cls]
    k = d(sides, rng)
    return k, max(1, k + add + bonus(attrs[2]))


def weapon_uc(weapon: dict, attrs: list[int]) -> int:
    """ÚČ = oprava SIL (u střelby OBR) + síla zbraně, nejméně 0."""
    idx = 1 if weapon.get("ranged") else 0
    return max(0, bonus(attrs[idx]) + int(weapon.get("attack", 0)))


def defense_oc(attrs: list[int], armor_quality: int, weapon_def: int, shield: int) -> int:
    """OČ = oprava OBR + kvalita zbroje + obrana zbraně (+1 se štítem)."""
    return bonus(attrs[1]) + armor_quality + weapon_def + shield


def wound(attack_total: int, defense_total: int, weapon_damage: int) -> int:
    """Zásah, pokud útok > obrana. Zranění = rozdíl + útočnost zbraně (nejméně 1)."""
    if attack_total <= defense_total:
        return 0
    return max(1, attack_total - defense_total + weapon_damage)


def trap(attr_bonus: int, danger: int, rng: random.Random | None = None) -> tuple[int, int, bool]:
    """Hod proti pasti: 1k10 + oprava vlastnosti; stejně nebo víc než nebezpečnost = štěstí."""
    k = d(10, rng)
    total = k + attr_bonus
    return k, total, total >= danger


def percent(chance: int, rng: random.Random | None = None) -> tuple[int, bool]:
    p = d(100, rng)
    return p, p <= chance


def combat_roll(rng: random.Random | None = None) -> list[int]:
    return open_d6(rng)
