"""Katalog výzbroje a výstroje DrD 1.6 (Pravidla pro začátečníky).

Váhy jsou v mincích (mn); 20 mn ≈ 1 kg. Ceny jsou podle pravidel jen orientační.
Zbraně: SZ = síla zbraně, Út = útočnost, OZ = obrana zbraně.
"""
from __future__ import annotations

MN_PER_KG = 20

# (název, SZ, útočnost, OZ, délka, váha mn, cena, skupina, poznámka)
MELEE_1H = [
    ("Dýka", 2, 0, -2, "1", 5, "1 zl", "lehká", ""),
    ("Tesák", 3, -1, -2, "1", 12, "4 zl", "lehká", ""),
    ("Krátký meč", 4, -1, -1, "1", 20, "16 zl", "lehká", ""),
    ("Obušek", 3, -2, -2, "1", 8, "2 st", "lehká", ""),
    ("Palcát", 3, 1, -1, "1", 20, "8 zl", "lehká", ""),
    ("Šavle", 4, 2, 1, "1", 25, "32 zl", "střední", ""),
    ("Široký meč", 5, 0, 0, "1", 30, "24 zl", "střední", "rodová zbraň člověka"),
    ("Sekera", 3, 1, -1, "1", 30, "10 st", "střední", "rodová zbraň kudůka"),
    ("Kyj", 3, 2, -1, "1", 35, "8 st", "střední", ""),
    ("Meč bastard", 6, 0, 1, "1", 40, "32 zl", "těžká", "rodová zbraň barbara"),
    ("Dlouhý meč", 7, -1, 0, "1–2", 50, "40 zl", "těžká", ""),
    ("Válečné kladivo", 5, 2, -1, "1", 50, "2 zl", "těžká", ""),
    ("Řemdih", 4, 3, -2, "1–2", 50, "1 zl", "těžká", ""),
]
MELEE_2H = [
    ("Okovaná hůl", 5, -1, 1, "2", 20, "7 st", "lehká", ""),
    ("Vidle", 4, 0, 1, "2", 50, "1 zl", "střední", ""),
    ("Kopí", 5, 0, 1, "1–2", 60, "1 zl", "střední", ""),
    ("Válečná sekera", 4, 3, -1, "1–2", 75, "4 zl", "střední", "ztrácí iniciativu; rodová zbraň trpaslíka"),
    ("Sudlice", 5, 1, 1, "2", 75, "1 zl", "střední", "ztrácí iniciativu"),
    ("Píka", 5, 2, 1, "2–3", 70, "1 zl 5 st", "střední", "ztrácí iniciativu"),
    ("Cep", 5, 4, -1, "2", 70, "8 st", "těžká", "ztrácí iniciativu"),
    ("Halapartna", 4, 6, 2, "2", 85, "4 zl", "těžká", "ztrácí iniciativu"),
    ("Obouruční meč", 7, 1, -1, "1–2", 85, "56 zl", "těžká", "ztrácí iniciativu"),
    ("Těžký kyj", 5, 4, -1, "1–2", 90, "2 zl", "těžká", "ztrácí iniciativu; rodová zbraň krolla"),
    ("Trojzubec", 6, 2, 2, "1–2", 95, "1 zl", "těžká", "ztrácí iniciativu"),
]
# Střelné: (název, SZ, útočnost, dostřel malý/střední/velký, váha mn, cena, poznámka)
RANGED = [
    ("Krátký luk", 4, 0, (10, 20, 30), 7, "4 zl", ""),
    ("Dlouhý luk", 5, 1, (15, 30, 50), 10, "16 zl", "jen rasy velikosti B a větší; rodová zbraň elfa"),
    ("Lehká kuše", 4, 1, (15, 27, 40), 20, "32 zl", "rodová zbraň hobita"),
    ("Těžká kuše", 6, 2, (19, 35, 55), 60, "44 zl", "jen rasy velikosti B a větší; střílí jednou za 2 kola"),
    ("Prak", 4, -1, (9, 16, 25), 5, "1 st", ""),
]
THROWN = [
    ("Vrhací dýka", 2, 0, (5, 9, 12), 5, "1 zl", "lehká"),
    ("Hvězdice", 3, -1, (3, 7, 11), 3, "6 st", "lehká"),
    ("Kámen", 1, 0, (7, 11, 15), 7, "0 zl", "lehká"),
    ("Flakónek (svěcená voda, lektvar)", 0, 0, (5, 9, 13), 5, "–", "lehká"),
    ("Láhev (olej, voda)", 0, 1, (4, 7, 10), 15, "–", "lehká"),
    ("Pochodeň (vrhací)", 0, 1, (4, 7, 10), 10, "1 md", "lehká"),
    ("Vrhací kopí", 5, 0, (5, 10, 15), 60, "1 zl", "střední"),
    ("Oštěp", 5, 1, (6, 14, 23), 12, "4 st", "střední"),
    ("Vrhací sekera", 3, 1, (4, 8, 12), 30, "10 st", "střední"),
    ("Vrhací vidle", 4, 0, (3, 5, 7), 50, "1 zl", "střední"),
]
RANGED_OZ = -2  # všechny střelné a vrhací zbraně mají OZ −2

# Zbroje: (název, KZ, váha A/B/C mn, cena A/B/C zl)
ARMORS = [
    ("Vycpávaná zbroj", 2, (35, 50, 60), (14, 16, 18)),
    ("Kožená zbroj", 3, (55, 80, 100), (16, 20, 24)),
    ("Šupinová zbroj", 4, (120, 170, 205), (100, 120, 135)),
    ("Kroužková zbroj", 5, (250, 350, 420), (240, 300, 340)),
    ("Plátová zbroj", 6, (280, 400, 480), (280, 350, 400)),
    ("Rytířská zbroj", 7, (350, 500, 600), (700, 800, 850)),
]
SHIELD = ("Štít", 1, (35, 50, 60), (4, 5, 6))
NO_ARMOR_KZ = 1  # Tabulka kvality zbroje: „žádné“ = kvalita 1

RACE_SIZE = {"Hobit": "A", "Kudůk": "A", "Trpaslík": "A", "Elf": "B", "Člověk": "B", "Barbar": "B", "Kroll": "C"}

# Výstroj: (název, váha mn, poznámka)
GEAR = [
    ("Kožená torna", 20, "unese 800 mn"),
    ("Velký vak", 12, "unese 500 mn"),
    ("Malý vak", 7, "unese 150 mn"),
    ("Měch na vodu (plný)", 25, "prázdný 5 mn, voda na den"),
    ("Flakónek (plný)", 5, "prázdný 3 mn"),
    ("Láhev (plná)", 15, "prázdná 5 mn"),
    ("Jídlo na týden", 175, "150–200 mn, sušené až pětina váhy"),
    ("Pochodeň", 10, "svítí 6 sáhů, vydrží 3 směny"),
    ("Lucerna", 30, "svítí 8 sáhů, 25–35 mn"),
    ("Láhev oleje", 15, "do lucerny na 4 hodiny, nebo jako zbraň"),
    ("Křesadlo", 2, "křemen, ocílka a troud"),
    ("Vlčí mor (svazeček)", 1, "proti lykantropům"),
    ("Svěcená voda (flakónek)", 5, "proti nemrtvým"),
    ("Hůl (1,5 sáhu)", 10, "na oťukávání podlahy"),
    ("Provaz (1 sáh)", 2, "prodává se na sáhy"),
    ("Zrcátko", 2, "kovové, kapesní"),
    ("Pergamen (10 svitků)", 1, ""),
    ("Kladivo", 15, ""),
    ("Železné hřebíky (tucet)", 2, ""),
    ("Šaty", 80, "40–120 mn podle druhu"),
    ("Šípy / šipky (10 ks)", 20, "1 st za 10 kusů, stříbrné 1 zl"),
    ("Toulec", 10, "na 10–20 šípů, asi 5 st"),
]

CATALOG_GROUPS = ["Zbraně na blízko", "Střelné a vrhací", "Zbroje a štít", "Výstroj"]


def kg(mn: float) -> float:
    return round(mn / MN_PER_KG, 2)


def catalog(race: str | None = None) -> list[dict]:
    """Položky katalogu jako šablony předmětů do batohu."""
    size = RACE_SIZE.get(race or "", "B")
    si = "ABC".index(size)
    out: list[dict] = []
    for rows, hands in ((MELEE_1H, "jednoruční"), (MELEE_2H, "obouruční")):
        for name, sz, ut, oz, length, mn, price, grp, note in rows:
            out.append({"group": "Zbraně na blízko", "name": name, "category": "Zbraň", "attack": sz,
                        "damage": ut, "defense": oz, "ranged": False, "weight_mn": mn, "price": price,
                        "info": f"{hands}, {grp} · délka {length}" + (f" · {note}" if note else "")})
    for name, sz, ut, rng, mn, price, note in RANGED:
        out.append({"group": "Střelné a vrhací", "name": name, "category": "Zbraň", "attack": sz, "damage": ut,
                    "defense": RANGED_OZ, "ranged": True, "weight_mn": mn, "price": price,
                    "info": f"střelná · dostřel {rng[0]}/{rng[1]}/{rng[2]} sáhů" + (f" · {note}" if note else "")})
    for name, sz, ut, rng, mn, price, grp in THROWN:
        out.append({"group": "Střelné a vrhací", "name": name, "category": "Zbraň", "attack": sz, "damage": ut,
                    "defense": RANGED_OZ, "ranged": True, "weight_mn": mn, "price": price,
                    "info": f"vrhací, {grp} · dostřel {rng[0]}/{rng[1]}/{rng[2]} sáhů"})
    for name, kz, weights, prices in ARMORS:
        out.append({"group": "Zbroje a štít", "name": name, "category": "Zbroj", "quality": kz,
                    "weight_mn": weights[si], "price": f"{prices[si]} zl",
                    "info": f"KZ {kz} · velikost {size}"})
    name, bonus, weights, prices = SHIELD
    out.append({"group": "Zbroje a štít", "name": name, "category": "Štít", "defense": bonus,
                "weight_mn": weights[si], "price": f"{prices[si]} zl",
                "info": f"+{bonus} k hodu na obranu · velikost {size}"})
    for name, mn, note in GEAR:
        out.append({"group": "Výstroj", "name": name, "category": "Ostatní", "weight_mn": mn, "price": "",
                    "info": note})
    for it in out:
        it["weight"] = kg(it["weight_mn"])
    return out


def carry_capacity_mn(sil_bonus: int) -> int:
    """Tabulka nosnosti: 360 mn při opravě 0, ±30 mn za každý bod opravy za sílu."""
    return 360 + 30 * int(sil_bonus)


# Tabulka naložení: (nejvýš násobek nosnosti, název, část pohyblivosti)
LOAD_LEVELS = [(1, "Bez naložení", "1"), (2, "Mírné naložení", "¾"), (3, "Střední naložení", "½"),
               (4, "Velké naložení – postih −1 k útoku", "¼")]
