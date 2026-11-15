"""Pravidla Dračího doupěte 1.6 (Pravidla pro začátečníky, ALTAR).

Tabulky z kapitol Tvoje postava, Pravidla pro boj a …a mimo boj.
Kostky: k6+ (boj), k10 (pasti), k% (schopnosti) a volné hody k4–k20.
"""
from __future__ import annotations

import random

from .common import d, fmt, open_d6

SYSTEM = "drd"
NAME = "Dračí doupě 1.6"
SHORT = "DrD 1.6"
DICE = ["k4", "k6", "k8", "k10", "k12", "k20", "k6+", "k%"]

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

# Tabulka hraničářovy magenergie (PPZ): úroveň 1–5, sloupce INT 6–7, 8–9, … 18–19
RANGER_MANA = {1: [0] * 7, 2: [3] * 7, 3: [6, 6, 7, 7, 7, 8, 8], 4: [10, 10, 11, 11, 11, 12, 13],
               5: [12, 13, 13, 14, 15, 15, 16]}
RANGER_MANA_COLS = [6, 8, 10, 12, 14, 16, 18]
# Tabulka alchymistovy magenergie (PPZ): úroveň 1–5, sloupce OBR 8–9, 10–11, 12–13, 14, 15–16, 17–18, 19–20
ALCH_MANA = {1: [7, 7, 8, 8, 8, 9, 9], 2: [15, 16, 17, 18, 19, 20, 21], 3: [31, 35, 38, 40, 42, 45, 49],
             4: [62, 70, 76, 80, 84, 90, 98], 5: [126, 131, 142, 150, 158, 169, 184]}
ALCH_MANA_COLS = [8, 10, 12, 14, 15, 17, 19]


def _col(value: int, starts: list[int]) -> int:
    col = 0
    for i, lo in enumerate(starts):
        if value >= lo:
            col = i
    return col


def class_mana(cls: str, level: int, attrs: list[int]) -> int | None:
    """Magenergie podle tabulek PPZ (kouzelník i dál podle PPP). None = povolání magenergii nemá.

    Hraničář a alchymista: tabulky končí 5. úrovní – výše se použije hodnota 5. úrovně (zbytek ručně).
    """
    if cls == "Kouzelník":
        from .drd_kouzla import wizard_mana
        return wizard_mana(level, attrs[3])
    lvl = max(1, min(5, int(level)))
    if cls == "Hraničář":
        return RANGER_MANA[lvl][_col(attrs[3], RANGER_MANA_COLS)]
    if cls == "Alchymista":
        return ALCH_MANA[lvl][_col(attrs[1], ALCH_MANA_COLS)]
    return None


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


# --- schopnosti povolání (Pravidla pro začátečníky, úrovně 1–5) -------------------

MAX_TABLE_LEVEL = 5

CLASS_DESC = {
    "Válečník": "Bojovník v první linii. Nejvíc životů (základ 10, k10 za úroveň).",
    "Hraničář": "Stopař a lovec s mimosmyslovými schopnostmi. Životy 8, k6+2 za úroveň.",
    "Alchymista": "Výrobce lektvarů a magických předmětů. Životy 7, k6+1 za úroveň.",
    "Kouzelník": "Sesílá kouzla za magenergii. Životy 6, k6 za úroveň.",
    "Zloděj": "Mistr převleků, zámků a pastí. Schopnosti se hází na k% (musí padnout šance nebo méně). "
              "Životy 6, k6 za úroveň.",
}

# Pravděpodobnost úspěchu zloděje: (název, hodnoty pro úroveň 1–5, [(vlastnost, násobek opravy)])
THIEF_TABLE: list[tuple[str, list[int], list[tuple[str, int]]]] = [
    ("Převleky", [5, 10, 15, 20, 25], [("CHA", 3)]),
    ("Získání důvěry", [7, 11, 15, 19, 23], [("CHA", 3)]),
    ("Objevení mechanismu", [10, 15, 20, 25, 30], [("OBR", 2)]),
    ("Objevení objektu", [15, 20, 25, 30, 35], [("OBR", 3)]),
    ("Zneškodnění mechanismu", [15, 20, 25, 30, 35], [("OBR", 2)]),
    ("Otevření objektu", [25, 30, 35, 40, 45], [("OBR", 3)]),
    ("Šplhání po zdech", [70, 72, 74, 76, 78], [("OBR", 1)]),
    ("Skok z výšky", [65, 68, 71, 74, 77], [("OBR", 1)]),
    ("Tichý pohyb", [15, 18, 21, 23, 26], [("OBR", 1)]),
    ("Schování se ve stínu", [30, 35, 40, 45, 50], [("OBR", 2)]),
    ("Vybírání kapes", [10, 13, 16, 19, 22], [("CHA", 1), ("OBR", 1)]),
]

# Ostatní povolání: (název, popis, od úrovně, text místo procent)
CLASS_FEATURES: dict[str, list[tuple[str, str, int, str]]] = {
    "Válečník": [
        ("Zastrašení", "k% podle bojovnosti soupeře (tabulka zastrašení)", 1, "k%"),
        ("Poznávání artefaktů", "bez procentového hodu", 1, "–"),
        ("Léčba vlastních zranění", "bez procentového hodu", 2, "–"),
        ("Odhad zbraně", "čas podle tabulky odhadu zbraně", 2, "–"),
        ("Odhad soupeře", "ÚČ, OČ a zranitelnost protivníka", 4, "–"),
        ("Více útoků za kolo", "útočí víckrát než jednou za kolo", 5, "–"),
    ],
    "Hraničář": [
        ("Bonus pro boj se zvířaty", "počítá se v souboji", 1, "aktivní"),
        ("Mimosmyslové schopnosti", "stojí magenergii", 2, "magy"),
    ],
    "Alchymista": [
        ("Odolávání jedům", "bez procentového hodu", 1, "–"),
        ("Vidění magenergie", "bez procentového hodu", 1, "–"),
        ("Alchymie (výroba předmětů)", "spotřebuje magy a suroviny", 1, "–"),
    ],
    "Kouzelník": [
        ("Kouzlení", "za magenergii, bez procentového hodu", 1, "–"),
        ("Odvracení nevídaného", "bez procentového hodu", 1, "–"),
        ("Povolání přítele", "bez procentového hodu", 3, "–"),
    ],
    "Zloděj": [],
}

RANGER_TRACKING = [("Stopování – volná příroda", "sníh, louka, vysoký les", 80),
                   ("Stopování – obtížný terén", "hustý les, džungle, skály", 50),
                   ("Stopování – uzavřené prostory", "místnost, chodba", 60)]


def class_abilities(cls: str, level: int, attrs: list[int], branch: str | None = None) -> list[dict]:
    """Schopnosti povolání pro danou úroveň (od 6. úrovně i schopnosti zvoleného oboru z PPP).

    Každá položka: name, sub, pct (int nebo None), text (když pct je None), from_level, locked.
    """
    from . import drd_obory

    lvl = max(1, min(MAX_TABLE_LEVEL, int(level)))
    out: list[dict] = []
    adv_table = None
    if int(level) >= drd_obory.ADV_LEVEL and branch in ("Lupič", "Sicco"):
        adv_table = drd_obory.LUPIC_TABLE if branch == "Lupič" else drd_obory.SICCO_TABLE
    if cls == "Zloděj" and adv_table:
        alvl = max(6, min(15, int(level)))
        for name, vals, deps in adv_table:
            base = vals[alvl - 6]
            add = sum(mult * bonus(attrs[ATTRS.index(a)]) for a, mult in deps)
            parts = " + ".join(f"{mult}× {a} {fmt(bonus(attrs[ATTRS.index(a)]))}" for a, mult in deps)
            out.append({"name": name, "sub": f"{branch} {alvl}. úr.: {base} %" + (f" + {parts}" if parts else ""),
                        "pct": max(1, min(99, base + add)), "text": None, "from_level": 1})
    elif cls == "Zloděj":
        for name, vals, deps in THIEF_TABLE:
            base = vals[lvl - 1]
            add = sum(mult * bonus(attrs[ATTRS.index(a)]) for a, mult in deps)
            parts = " + ".join(f"{mult}× {a} {fmt(bonus(attrs[ATTRS.index(a)]))}" for a, mult in deps)
            out.append({"name": name, "sub": f"tabulka {base} % + {parts}", "pct": max(1, min(99, base + add)),
                        "text": None, "from_level": 1})
    elif cls == "Hraničář":
        for name, terrain, base in RANGER_TRACKING:
            out.append({"name": name, "sub": f"{terrain}: {base} % + 2 % × úroveň",
                        "pct": min(99, base + 2 * int(level)), "text": None, "from_level": 1})
        out.append({"name": "Hraničářův pes", "sub": "šance při postupu na úroveň", "pct": 40, "text": None,
                    "from_level": 1})
    for name, sub, frm, text in CLASS_FEATURES.get(cls, []):
        out.append({"name": name, "sub": sub, "pct": None, "text": text, "from_level": frm})
    if branch and int(level) >= drd_obory.ADV_LEVEL:
        for b in drd_obory.BRANCHES.get(cls, []):
            if b[0] != branch:
                continue
            for name, frm, sub in b[2]:
                out.append({"name": name, "sub": f"{branch} · {sub}", "pct": None, "text": "–", "from_level": frm,
                            "branch": branch})
    for a in out:
        a["locked"] = a["from_level"] > int(level)
    return out


def class_note(cls: str) -> str:
    if cls == "Zloděj":
        return ("Hodnoty z tabulky Pravděpodobnost úspěchu zloděje (úrovně 1–5) + násobek opravy vlastnosti. "
                "PJ může šanci upravit podle situace.")
    if cls == "Hraničář":
        return ("Za každou další stopovanou bytost +3 %, za každých 24 hodin stáří stopy −10 %. "
                "Pravidla pro začátečníky pokrývají úrovně 1–5.")
    return "Schopnosti bez procent se ověřují jinak (k6, tabulka nebo rozhodnutí PJ)."

