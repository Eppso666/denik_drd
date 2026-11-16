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

# Pravidla pro pokročilé, úroveň 6–15 (druid, chodec: sloupce INT jako u hraničáře)
DRUID_MANA = {6: [18, 19, 19, 20, 22, 23, 24], 7: [22, 23, 23, 24, 25, 26, 26], 8: [26, 27, 27, 29, 30, 31, 32],
              9: [30, 31, 31, 34, 35, 36, 39], 10: [35, 36, 36, 39, 40, 42, 44], 11: [40, 40, 41, 43, 44, 45, 48],
              12: [46, 46, 47, 50, 50, 53, 55], 13: [50, 50, 51, 55, 55, 58, 61], 14: [56, 57, 59, 62, 63, 66, 70],
              15: [62, 62, 64, 69, 69, 71, 76]}
CHODEC_MANA = {6: [15, 16, 16, 17, 18, 19, 20], 7: [18, 19, 19, 20, 21, 22, 22], 8: [21, 22, 22, 23, 24, 25, 25],
               9: [24, 25, 25, 27, 28, 29, 31], 10: [27, 28, 28, 30, 31, 32, 34], 11: [31, 31, 31, 33, 34, 35, 37],
               12: [34, 34, 34, 37, 37, 39, 41], 13: [37, 37, 38, 41, 41, 43, 45], 14: [40, 40, 42, 45, 45, 47, 50],
               15: [44, 44, 46, 49, 49, 51, 54]}
# Alchymista (theurg i pyrofor) 6–9 podle OBR; od 9. úrovně si magenergii destiluje sám
ALCH_MANA_ADV = {6: [184, 201, 218, 230, 242, 259, 276], 7: [256, 280, 303, 320, 337, 360, 384],
                 8: [360, 394, 426, 450, 474, 506, 540], 9: [490, 525, 568, 600, 632, 675, 710]}


def _col(value: int, starts: list[int]) -> int:
    col = 0
    for i, lo in enumerate(starts):
        if value >= lo:
            col = i
    return col


def class_mana(cls: str, level: int, attrs: list[int], branch: str | None = None) -> int | None:
    """Magenergie podle tabulek PPZ (1.–5. úroveň) a PPP podle oboru (6.–15. úroveň).

    None = povolání magenergii nemá. Dokud postava na 6.+ úrovni nemá zvolený obor, platí hodnota 5. úrovně.
    Alchymista: tabulka PPP končí 9. úrovní, potom si magenergii destiluje sám (zadává se ručně).
    """
    level = int(level)
    if cls == "Kouzelník":  # mág i čaroděj mají společnou tabulku
        from .drd_kouzla import wizard_mana
        return wizard_mana(level, attrs[3])
    lvl = max(1, min(5, level))
    if cls == "Hraničář":
        col = _col(attrs[3], RANGER_MANA_COLS)
        if level >= 6 and branch in ("Druid", "Chodec"):
            table = DRUID_MANA if branch == "Druid" else CHODEC_MANA
            return table[min(15, level)][col]
        return RANGER_MANA[lvl][col]
    if cls == "Alchymista":
        col = _col(attrs[1], ALCH_MANA_COLS)
        if level >= 6 and branch in ("Theurg", "Pyrofor"):
            return ALCH_MANA_ADV[min(9, level)][col]
        return ALCH_MANA[lvl][col]
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
    """Obrana celkem = OČ (oprava OBR + kvalita zbroje, nejméně 0) + obrana zbraně + štít."""
    return max(0, bonus(attrs[1]) + armor_quality) + weapon_def + shield


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


def pct_outcome(roll: int, chance: int, level: int = 1) -> tuple[bool, str | None]:
    """Výsledek hodu k%: (úspěch, zvláštní výsledek).

    Fatální neúspěch: číslo dělitelné deseti větší než šance (PPZ s. 82; 100 = „00“).
    Totální úspěch: od 6. úrovně číslo dělitelné deseti menší než šance (PPP s. 5).
    """
    ok = roll <= chance
    if roll % 10 == 0 and roll > chance:
        return False, "fatální neúspěch"
    if roll % 10 == 0 and roll < chance and int(level) >= 6:
        return True, "totální úspěch"
    return ok, None


def pct_text(roll: int, chance: int, level: int = 1) -> tuple[bool, str]:
    ok, special = pct_outcome(roll, chance, level)
    word = special.capitalize() if special else ("Úspěch" if ok else "Neúspěch")
    return ok, f"{word} – padlo {roll}, šance {chance} %"


# --- souboj: velikost, bojeschopnost, naložení (PPZ s. 71–72) ---------------------------------

SIZES = ["A0", "A", "B", "C", "D", "E"]
# Tabulka rozdílu velikostí: řádek = velikost obránce, sloupec = velikost útočníka
SIZE_DIFF = {
    "A0": [0, 2, 3, 4, 0, -2],
    "A": [-2, 0, 1, 2, 0, -1],
    "B": [-3, -1, 0, 1, 2, 0],
    "C": [-4, -2, -1, 0, 1, 2],
    "D": [-5, -3, -2, -1, 0, 1],
    "E": [-7, -4, -3, -2, -1, 0],
}
RACE_SIZE = {"Hobit": "A", "Kudůk": "A", "Trpaslík": "A", "Elf": "B", "Člověk": "B", "Barbar": "B", "Kroll": "C"}


def size_mod(attacker: str, defender: str) -> int:
    """Oprava hodu na útok tváří v tvář podle Tabulky rozdílu velikostí."""
    if attacker not in SIZES or defender not in SIZES:
        return 0
    return SIZE_DIFF[defender][SIZES.index(attacker)]


def ranged_size_mod(defender: str) -> int:
    """Střelba: na cíl velikosti D nebo E +1 (u A0 postih určí PJ)."""
    return 1 if defender in ("D", "E") else 0


# Tabulka bojeschopnosti: (odolnost do, část životů pro mez vyřazení / None = 1 život, postih)
FITNESS = [(5, 4, -3), (11, 6, -2), (16, 8, -1), (99, None, 0)]


def _fitness_row(odl: int) -> tuple[int | None, int]:
    for top, div, pen in FITNESS:
        if odl <= top:
            return div, pen
    return None, 0


def knockout_limit(hp_max: int, odl: int) -> int:
    """Mez vyřazení: část maxima životů podle odolnosti, zaokrouhleno aritmeticky, nejméně 1 život."""
    div, _ = _fitness_row(odl)
    if not div:
        return 1
    return max(1, int(hp_max / div + 0.5))


def wound_penalty(hp: int, hp_max: int, odl: int) -> int:
    """Postih k útoku i obraně, má-li postava méně než třetinu životů."""
    _, pen = _fitness_row(odl)
    return pen if hp_max > 0 and hp * 3 < hp_max else 0


def is_knocked_out(hp: int, hp_max: int, odl: int) -> bool:
    return hp <= knockout_limit(hp_max, odl)


# Od 10. úrovně pevný přírůstek životů bez opravy za odolnost (PPP s. 5, Tabulka růstu životů)
HP_FIXED = {"Válečník": 2, "Hraničář": 2, "Alchymista": 1, "Kouzelník": 1, "Zloděj": 1}
HP_FIXED_LEVEL = 10

# Tabulka zkušenosti (PPZ s. 32 pro 1.–6., PPP s. 5 pro 7.–16.): úroveň -> (zkušenost, cena výcviku v zl)
_XP = {
    "Válečník": [0, 450, 900, 1825, 3675, 7400, 15000, 30000, 55000, 83000, 114000, 148000, 185000, 225000, 268000, 314000],
    "Hraničář": [0, 525, 1050, 2075, 4125, 8225, 16350, 32500, 57500, 85500, 116500, 150500, 187500, 227500, 270500, 316500],
    "Alchymista": [0, 575, 1150, 2300, 4650, 9325, 18700, 37500, 62500, 90500, 121500, 155500, 192500, 232500, 275500, 321500],
    "Kouzelník": [0, 610, 1250, 2575, 5250, 10750, 22000, 45000, 70000, 98000, 129000, 163000, 200000, 240000, 283000, 329000],
    "Zloděj": [0, 325, 730, 1575, 3450, 7450, 16150, 35000, 60000, 88000, 119000, 153000, 190000, 230000, 273000, 319000],
}
_XP_COST = {
    "Válečník": [0, 2, 4, 8, 13, 19, 26, 34, 43, 53, 64, 77, 90, 105, 120, 137],
    "Hraničář": [0, 2, 4, 8, 13, 19, 26, 34, 44, 54, 66, 78, 92, 107, 123, 140],
    "Alchymista": [0, 2, 4, 8, 13, 19, 26, 35, 44, 55, 67, 79, 94, 109, 125, 142],
    "Kouzelník": [0, 2, 4, 8, 13, 19, 27, 35, 45, 55, 67, 80, 94, 110, 126, 144],
    "Zloděj": [0, 2, 4, 8, 12, 18, 25, 32, 41, 51, 61, 73, 86, 99, 114, 130],
}
MAX_XP_LEVEL = 16


def xp_for_level(cls: str, level: int) -> int | None:
    """Zkušenost potřebná pro danou úroveň (None = tabulka nesahá tak vysoko)."""
    row = _XP.get(cls)
    if not row or not 1 <= int(level) <= MAX_XP_LEVEL:
        return None
    return row[int(level) - 1]


def training_cost(cls: str, level: int) -> int | None:
    row = _XP_COST.get(cls)
    if not row or not 1 <= int(level) <= MAX_XP_LEVEL:
        return None
    return row[int(level) - 1]


def level_for_xp(cls: str, xp: int) -> int:
    row = _XP.get(cls, _XP["Válečník"])
    return max(i + 1 for i, v in enumerate(row) if xp >= v)


# Pohyblivost a postřeh (PPZ s. 83 a 86)
RACE_MOVE = {"Hobit": 10, "Kudůk": 9, "Trpaslík": 8, "Elf": 12, "Člověk": 11, "Barbar": 12, "Kroll": 11}
LOAD_MOVE = [(1, 1.0), (2, 0.75), (3, 0.5), (4, 0.25)]


def base_movement(race: str, attrs: list[int]) -> int:
    return RACE_MOVE.get(race, 11) + bonus(attrs[1]) + 2 * bonus(attrs[0])


def movement(race: str, attrs: list[int], load_ratio: float) -> int:
    """Okamžitá pohyblivost podle naložení (čtvrtiny se zaokrouhlují nahoru)."""
    import math
    base = base_movement(race, attrs)
    part = next((p for top, p in LOAD_MOVE if load_ratio <= top), 0.25)
    return max(1, math.ceil(base * part))


def perception(race: str, attrs: list[int]) -> tuple[int, int]:
    """Postřeh (k%): na objekty = INT (+5 kroll, barbar, trpaslík); na mechanismy = INT/2 (+5 elf, hobit, kudůk)."""
    intel = attrs[3]
    obj = intel + (5 if race in ("Kroll", "Barbar", "Trpaslík") else 0)
    mech = intel // 2 + (5 if race in ("Elf", "Hobit", "Kudůk") else 0)
    return obj, mech


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

