"""Pomůcky Pána jeskyně z Příručky PJ DrD 1.6 (PPZ PJ, s. 101–112).

Jen čísla a krátké připomínky vlastními slovy s odkazem na stranu – ne texty pravidel.
Tyto údaje se ukazují jen Pánu jeskyně (kromě mechaniky hodu, kterou hráč potřebuje v Kostkách).
"""
from __future__ import annotations

import math

# --- rasové schopnosti: poznámky pro PJ (PPZ PJ s. 101–102) ---------------------------------
RACE_SPECIAL_GM = {
    "Hobit": "Ve spánku čich nepoužívá, silná přítomnost tvora ho ale může probudit.",
    "Trpaslík": "Ve spánku infravidění nefunguje (zavřená víčka); oslepený trpaslík ho nemá.",
    "Kroll": "Ve spánku ultrasluch vyřazen; používá ho jen vědomě – napověz, když by ho zjevně použil.",
}
RACE_SPECIAL_PAGE = "PPZ PJ s. 101–102"

# --- rychlost a cestování (PPZ PJ s. 109) ----------------------------------------------------
TRAVEL_NOTE = ("Tabulky cestování platí pro jezdeckého koně nebo dobrodruha s pohyblivostí 14 a odolností 14. "
               "Družina jde tak rychle jako její nejpomalejší postava.")
# Tabulka nutného náskoku: prostředí → náskok (1 stupeň ≈ 5 sáhů)
LEAD = [("bludiště", 2), ("podzemí", 4), ("les", 6), ("louka", 8), ("poušť", 10), ("cesta", 12), ("město", 3),
        ("palác", 3)]
LEAD_PAGE = "PPZ PJ s. 109"


def lead_needed(distance_sahu: float) -> int:
    """Kolik stupňů náskoku dává vzdálenost v sázích (dělit pěti)."""
    return int(distance_sahu // 5)


# --- postřeh a naslouchání (PPZ PJ s. 110) ---------------------------------------------------
# Tabulka nápadnosti věcí: (věc, palác, podzemí) – hodnota v % a druh (mech. = mechanismus, objekt)
NOTICE_THINGS = [
    ("tajné dveře jako součást zdi (1×1½ sáhu)", (5, "mech."), (0, "objekt")),
    ("tajné tlačítko, které je ovládá", (-15, "mech."), (0, "mech.")),
    ("tajná schránka ve zdi (¼×¼ sáhu)", (-15, "mech."), (-10, "mech.")),
    ("skrýš za obrazem nebo nábytkem", (25, "objekt"), (25, "objekt")),
    ("past spuštěná první postavou (šipka, kámen)", (-5, "mech."), (0, "mech.")),
    ("propadliště", (5, "mech."), (10, "objekt")),
]
# Tabulka nápadnosti zvuků (pro naslouchání hned za dveřmi)
NOTICE_SOUNDS = [("skřetí hostina v pokročilém stádiu", 150), ("chrápající drak", 125), ("křik", 100),
                 ("obvyklý hovor", 75), ("tichý hovor", 50), ("chůze", 30), ("skřípání otvíraných dveří", 25),
                 ("šeptání", 10), ("ticho", 0)]
NOTICE_PAGE = "PPZ PJ s. 110"
SOUND_PER_SAH = -1      # každý sáh dál −1 %
SOUND_PER_DOOR = -30    # každé dřevěné dveře mezi zdrojem a družinou −30 %
SOUND_AGAIN = 10        # znovu zaslechnout už slyšený zvuk +10 %
KNOWN_SECRET = 50       # ví, že tam tajné dveře jsou (bez podrobností): +50 % k postřehu (s. 111)


def notice_from_shifts(shifts: float, perception: int = 10) -> int:
    """Nápadnost z odhadu, za kolik směn by věc někdo našel: 100 / směny − postřeh (orientačně 10 %)."""
    return int(round(100 / max(0.1, shifts) - perception))


def sound_notice(base: int, sahu: int = 0, doors: int = 0, again: bool = False) -> int:
    return base + SOUND_PER_SAH * int(sahu) + SOUND_PER_DOOR * int(doors) + (SOUND_AGAIN if again else 0)


# --- dveře (PPZ PJ s. 111) ---------------------------------------------------------------------
# druh dveří → (název, nebezpečnost pasti od–do, ztráta životů při neúspěchu od–do)
DOORS = [("I", "Dřevěné", (6, 8), (0, 1)), ("II", "Bytelné dřevěné", (8, 11), (0, 2)),
         ("III", "Železné", (12, 15), (0, 5)), ("IV", "Kamenné", (15, 18), (0, 9))]
DOORS_PAGE = "PPZ PJ s. 111"
DOOR_NOTES = ("Hodnoty platí pro zamčené dveře; jen vzpříčené asi poloviční, zatarasené asi dvojnásobné. "
              "Brána +2 až 3. Kdo dveře zevnitř drží: +1 + jeho oprava za sílu (aspoň +1). "
              "Hod o 1 nižší než potřeba: past dveří klesne o 1. Kouzlo zamkni: +8 (dřevěné 14–16, s. 112).")
WEAPON_KINDS = ["ostré bodné", "ostré drtivé", "tupé drtivé"]
# Tabulka vyražení dveří: druh dveří → pro každý druh zbraně (násobek SZ k bonusu, násobek rozdílu jako poškození)
DOOR_WEAPON = {
    "I": [(0.5, 0), (2, 0), (1, 0)],
    "II": [(0.25, 0.5), (1, 0), (1, 0)],
    "III": [(0, 1), (0.5, 0.5), (1, 0.25)],
    "IV": [(0, 2), (0.5, 1), (0.5, 0.5)],
}
# poškození zbraně podle materiálu: (−1 útočnost do, −2 útočnost do; víc = zničena)
WEAPON_MATERIAL = {"dřevěná": (3, 6), "okovaná": (4, 8), "kovová": (5, 11)}


def door(code: str) -> tuple:
    return next(d for d in DOORS if d[0] == code)


def door_weapon_bonus(code: str, kind: str, sz: int) -> int:
    """Bonus k hodu proti pasti dveří za zbraň: násobek SZ (zaokrouhleno dolů)."""
    f, _ = DOOR_WEAPON[code][WEAPON_KINDS.index(kind)]
    return int(math.floor(f * int(sz)))


def door_weapon_damage(code: str, kind: str, missed_by: int) -> int:
    """„Životy“, o které zbraň přijde při neúspěchu: násobek rozdílu, zaokrouhleno nahoru."""
    _, f = DOOR_WEAPON[code][WEAPON_KINDS.index(kind)]
    return int(math.ceil(f * max(0, int(missed_by))))


def weapon_damage_effect(material: str, lost: int) -> str:
    a, b = WEAPON_MATERIAL[material]
    if lost <= 0:
        return "zbraň vydržela"
    if lost <= a:
        return "útočnost zbraně −1"
    if lost <= b:
        return "útočnost zbraně −2"
    return "zbraň je zničena"


# --- snížení úrovně (PPZ PJ s. 112) ------------------------------------------------------------
LEVEL_DRAIN_PAGE = "PPZ PJ s. 112"
LEVEL_DRAIN_NOTE = ("Hody, pravděpodobnosti a tabulkové hodnoty podle nižší úrovně; kouzla, životy a dovednosti "
                    "zůstávají. Zkušenosti: o 1 méně, než je potřeba na ztracenou úroveň. Okamžitá magenergie "
                    "zůstane, další meditace už dá méně.")


def drain_level(c: dict) -> str | None:
    """Postava ztratí jednu úroveň (dotyk nemrtvého apod.). Vrací popis změny, nebo None (už je na 1. úrovni)."""
    from . import drd
    lvl = int(c.get("level", 1))
    if lvl <= 1:
        return None
    need = drd.xp_for_level(c.get("cls", ""), lvl)
    c["level"] = lvl - 1
    old_xp = int(c.get("xp", 0))
    if need:
        c["xp"] = min(old_xp, need - 1)
    c["xp_next"] = drd.xp_for_level(c.get("cls", ""), lvl) or c.get("xp_next", 0)
    table = drd.class_mana(c.get("cls", ""), lvl - 1, c.get("attrs") or [10] * 5, c.get("branch"))
    if table is not None and c.get("cls") != "Alchymista":
        c["mana_max"] = table  # okamžitá magenergie (c["mana"]) zůstává
    c["drained_from"] = max(int(c.get("drained_from") or 0), lvl)
    return f"Úroveň {lvl} → {lvl - 1} · zkušenosti {old_xp} → {c['xp']}"
