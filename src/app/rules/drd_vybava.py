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
# Kombinace dvou jednoručních zbraní (tabulka obouručních zbraní PPZ): váha i cena jsou součtem obou dílů,
# díly lze používat i jednotlivě. (název, SZ, útočnost, OZ, délka, díly, skupina)
COMBOS = [
    ("Dvě dýky", 3, 1, 2, "1", ("Dýka", "Dýka"), "lehká"),
    ("Tesák a dýka", 4, 0, 2, "1", ("Tesák", "Dýka"), "střední"),
    ("Krátký meč a dýka", 5, 0, 3, "1", ("Krátký meč", "Dýka"), "střední"),
    ("Dvě šavle", 8, -2, 3, "1", ("Šavle", "Šavle"), "těžká"),
    ("Široký meč a dýka", 5, 1, 2, "1", ("Široký meč", "Dýka"), "těžká"),
    ("Široký meč a tesák", 6, -2, 2, "1", ("Široký meč", "Tesák"), "těžká"),
]


def _price_zl(price: str) -> float:
    zl = st = 0
    for num, unit in __import__("re").findall(r"(\d+)\s*(zl|st)", price):
        if unit == "zl":
            zl += int(num)
        else:
            st += int(num)
    return zl + st / 10


def _fmt_zl(v: float) -> str:
    zl, st = int(v), round((v - int(v)) * 10)
    return f"{zl} zl" + (f" {st} st" if st else "")


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

# Rodové zbraně (PPZ s. 68): +1 k útočnému číslu
RODOVE = {"Hobit": "Lehká kuše", "Kudůk": "Sekera", "Trpaslík": "Válečná sekera", "Elf": "Dlouhý luk",
          "Člověk": "Široký meč", "Barbar": "Meč bastard", "Kroll": "Těžký kyj"}
UNARMED_OZ = -3  # Tabulka zbraní: „žádná“ – síla 0, útočnost 0, obrana −3 (se samotným štítem 0)

RACE_SIZE = {"Hobit": "A", "Kudůk": "A", "Trpaslík": "A", "Elf": "B", "Člověk": "B", "Barbar": "B", "Kroll": "C"}

# Výstroj podle Ceníku PPZ s. 101 (Příručka PJ) a kapitoly Výstroj z Pravidel pro začátečníky.
# (název, váha mn, cena, poznámka, skupina). Cena „až“/„–“ = rozpětí (koupí se za dolní mez, lze upravit),
# „?“ = cena se velmi liší, určí PJ. * = neprodává se všude, záleží na PJ.
G_GEAR, G_FOOD, G_MISC = "Výstroj", "Jídlo a služby", "Oblečení a zvířata"
GEAR = [
    ("Kožená torna", 20, "5 zl 5 st", "unese 800 mn", G_GEAR),
    ("Velký vak", 12, "8 st", "unese 500 mn", G_GEAR),
    ("Malý vak", 7, "4 st", "unese 150 mn", G_GEAR),
    ("Měch na vodu", 5, "1 st 5 md", "prázdný; plný 25 mn, voda na den", G_GEAR),
    ("Flakónek", 3, "4 st", "prázdný; plný 5 mn", G_GEAR),
    ("Láhev (½ čtvrtky)", 5, "1 st", "prázdná; plná 15 mn", G_GEAR),
    ("Pochodně (6 ks)", 60, "6 md", "svítí 6 sáhů, vydrží 3 směny", G_GEAR),
    ("Lucerna obyčejná", 24, "3 st 5 md", "svítí 8 sáhů", G_GEAR),
    ("Lucerna s okenicemi", 35, "1 zl 5 st", "svítí 8 sáhů, lze zaclonit", G_GEAR),
    ("Olej (½ čtvrtky)", 10, "3 st 2 md", "do lucerny na 4 hodiny, nebo jako zbraň", G_GEAR),
    ("Křesadlo", 2, "1 st", "křemen, ocílka a troud", G_GEAR),
    ("Vlčí mor (svazeček)", 1, "?", "proti lykantropům; cena se velmi liší", G_GEAR),
    ("Svěcená voda (0,1 čtvrtky)", 2, "1 zl", "proti nemrtvým; neprodává se všude*", G_GEAR),
    ("Hůl (1,5 sáhu)", 10, "2 st 3 md", "na oťukávání podlahy", G_GEAR),
    ("Provaz (10 sáhů)", 20, "9 st 5 md", "", G_GEAR),
    ("Zrcátko kovové", 2, "1 st", "kapesní", G_GEAR),
    ("Pergamen (20×30 coulů)", 0.1, "4 zl", "", G_GEAR),
    ("Nepravý pergamen", 0.1, "8 st", "", G_GEAR),
    ("Kladivo", 15, "4 st", "", G_GEAR),
    ("Hřebíky (30 ks)", 5, "1 st", "", G_GEAR),
    ("Pila", 10, "5–15 st", "5–15 mn podle velikosti", G_GEAR),
    ("Zlodějské náčiní", 20, "?", "neprodává se všude*, cena se velmi liší", G_GEAR),
    ("Truhla malá dřevěná", 50, "4 zl", "", G_GEAR),
    ("Truhla velká železná", 1500, "16 zl", "", G_GEAR),
    ("Deka, houně", 40, "1–8 zl", "20–60 mn", G_GEAR),
    ("Šípy / šipky (10 ks)", 20, "1 st", "stříbrné 1 zl za 10 ks", G_GEAR),
    ("Toulec", 10, "5 st", "na 10–20 šípů; cena orientační", G_GEAR),
    ("Jídlo na týden – skromné", 150, "2 zl 3 st", "sušené až pětina váhy", G_FOOD),
    ("Jídlo na týden – dobré", 200, "5 zl 5 st", "sušené až pětina váhy", G_FOOD),
    ("Víno (1 čtvrtka)", 20, "4 st", "", G_FOOD),
    ("Pivo (soudek, 5 čtvrtek)", 120, "5 st 5 md", "", G_FOOD),
    ("Medovina (0,3 čtvrtky)", 6, "3 st", "", G_FOOD),
    ("Večeře v hostinci", 0, "5 st až 3 zl", "služba", G_FOOD),
    ("Nocleh v hostinci", 0, "1–3 zl", "podle luxusu; služba", G_FOOD),
    ("Živobytí v podnájmu (týden)", 0, "20 zl", "cca, včetně stravy; bez zvláštních výdajů (oblečení…)", G_FOOD),
    ("Živobytí doma (týden)", 0, "8 zl", "střední životní úroveň; bez zvláštních výdajů", G_FOOD),
    ("Šaty letní obyčejné", 40, "8 zl", "", G_MISC),
    ("Šaty letní zdobené", 60, "80 zl", "", G_MISC),
    ("Šaty zimní obyčejné", 80, "20 zl", "", G_MISC),
    ("Šaty zimní zdobené", 120, "180 zl", "", G_MISC),
    ("Sedlo", 65, "30–50 zl", "50–80 mn", G_MISC),
    ("Mezek", 4000, "40 zl", "zvíře", G_MISC),
    ("Kůň", 13000, "50–1000 zl", "zvíře; cena podle kvality", G_MISC),
    ("Trakař nebo dvoukolák", 250, "3–5 zl", "", G_MISC),
    ("Kočár pro 4 osoby", 5000, "2000–6000 zl", "", G_MISC),
]
GEAR_SOURCE = "PPZ s. 101"
NOT_IN_CENIK = {"Šípy / šipky (10 ks)", "Toulec"}  # z kapitoly Výstroj, ne z Ceníku
START_MONEY_ZL = 85  # PPZ s. 101, Peníze: dobrodruzi začínají asi s 85 zl

CATALOG_GROUPS = ["Zbraně na blízko", "Střelné a vrhací", "Zbroje a štít", G_GEAR, G_FOOD, G_MISC]


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
                        "hands": 2 if hands == "obouruční" else 1,
                        "info": f"{hands}, {grp} · délka {length}" + (f" · {note}" if note else "")})
    one = {r[0]: r for r in MELEE_1H}
    for name, sz, ut, oz, length, parts, grp in COMBOS:
        mn = sum(one[p][5] for p in parts)
        price = _fmt_zl(sum(_price_zl(one[p][6]) for p in parts))
        out.append({"group": "Zbraně na blízko", "name": name, "category": "Zbraň", "attack": sz, "damage": ut,
                    "defense": oz, "ranged": False, "weight_mn": mn, "price": price, "hands": 2,
                    "info": f"kombinace dvou jednoručních zbraní ({' + '.join(parts)}), {grp} · délka {length}"})
    for name, sz, ut, rng, mn, price, note in RANGED:
        out.append({"group": "Střelné a vrhací", "name": name, "category": "Zbraň", "attack": sz, "damage": ut,
                    "defense": RANGED_OZ, "ranged": True, "weight_mn": mn, "price": price, "range": list(rng),
                    "hands": 2, "info": f"střelná · dostřel {rng[0]}/{rng[1]}/{rng[2]} sáhů" + (f" · {note}" if note else "")})
    for name, sz, ut, rng, mn, price, grp in THROWN:
        out.append({"group": "Střelné a vrhací", "name": name, "category": "Zbraň", "attack": sz, "damage": ut,
                    "defense": RANGED_OZ, "ranged": True, "weight_mn": mn, "price": price, "range": list(rng),
                    "info": f"vrhací, {grp} · dostřel {rng[0]}/{rng[1]}/{rng[2]} sáhů"})
    for name, kz, weights, prices in ARMORS:
        out.append({"group": "Zbroje a štít", "name": name, "category": "Zbroj", "quality": kz,
                    "weight_mn": weights[si], "price": f"{prices[si]} zl",
                    "info": f"KZ {kz} · velikost {size}"})
    name, bonus, weights, prices = SHIELD
    out.append({"group": "Zbroje a štít", "name": name, "category": "Štít", "defense": bonus,
                "weight_mn": weights[si], "price": f"{prices[si]} zl",
                "info": f"+{bonus} k hodu na obranu · velikost {size}"})
    for name, mn, price, note, grp in GEAR:
        out.append({"group": grp, "name": name, "category": "Ostatní", "weight_mn": mn, "price": price,
                    "info": " · ".join(x for x in (note, "" if name in NOT_IN_CENIK else GEAR_SOURCE) if x)})
    for it in out:
        it["weight"] = kg(it["weight_mn"])
    return out


def carry_capacity_mn(sil_bonus: int) -> int:
    """Tabulka nosnosti: 360 mn při opravě 0, ±30 mn za každý bod opravy za sílu."""
    return 360 + 30 * int(sil_bonus)


# Tabulka naložení: (nejvýš násobek nosnosti, název, část pohyblivosti)
LOAD_LEVELS = [(1, "Bez naložení", "1"), (2, "Mírné naložení", "¾"), (3, "Střední naložení", "½"),
               (4, "Velké naložení – postih −1 k útoku", "¼")]


# --- omezení výzbroje podle povolání (PPZ, kapitoly povolání) ----------------------------------
# skupiny zbraní pro boj tváří v tvář, které povolání ovládá; vrhací; střelné; zbroje; štít
CLASS_GEAR = {
    "Válečník": {"melee": {"lehká", "střední", "těžká"}, "thrown": {"lehká", "střední"}, "ranged": "all",
                 "armor": "all", "shield": True},
    "Hraničář": {"melee": {"lehká", "střední"}, "thrown": {"lehká", "střední"}, "ranged": "no_heavy",
                 "armor": {"Vycpávaná zbroj", "Kožená zbroj", "Šupinová zbroj", "Kroužková zbroj"}, "shield": True},
    "Alchymista": {"melee": {"lehká"}, "thrown": {"lehká"}, "ranged": "no_heavy",
                   "armor": {"Vycpávaná zbroj", "Kožená zbroj", "Šupinová zbroj"}, "shield": False},
    "Kouzelník": {"melee": {"lehká"}, "thrown": {"lehká"}, "ranged": "none", "armor": set(), "shield": False},
    "Zloděj": {"melee": {"lehká", "střední"}, "thrown": {"lehká", "střední"}, "ranged": "no_heavy",
               "armor": {"Vycpávaná zbroj", "Kožená zbroj"}, "shield": False},
}
CLASS_GEAR_TEXT = {
    "Válečník": "všechny zbraně, všechna brnění i štít",
    "Hraničář": "lehké a střední zbraně, střelné a vrhací kromě těžké kuše, brnění kromě plátové a rytířské, štít",
    "Alchymista": "lehké zbraně a lehké vrhací, střelné kromě těžké kuše, vycpávané, kožené či šupinové brnění, bez štítu",
    "Kouzelník": "jen lehké zbraně (i vrhací), žádné střelné zbraně, štít ani zbroj",
    "Zloděj": "lehké a střední zbraně, vrhací, střelné kromě těžké kuše, vycpávané či kožené brnění, bez štítu",
}


def _weapon_kind(name: str) -> tuple[str, str] | None:
    n = name.strip().lower()
    for rows in (MELEE_1H, MELEE_2H):
        for r in rows:
            if r[0].lower() == n:
                return "melee", r[7]
    for r in COMBOS:
        if r[0].lower() == n:
            return "melee", r[6]
    for r in RANGED:
        if r[0].lower() == n:
            return "ranged", "heavy" if r[0] == "Těžká kuše" else "ok"
    for r in THROWN:
        if r[0].lower() == n:
            return "thrown", r[6]
    return None


def gear_problem(cls: str, item: dict) -> str | None:
    """Text upozornění, když povolání předmět z pravidel neovládá; None = v pořádku nebo neznámý předmět."""
    rules = CLASS_GEAR.get(cls)
    if not rules:
        return None
    name = item.get("name", "")
    cat = item.get("category")
    if cat == "Zbraň":
        kind = _weapon_kind(name)
        if not kind:
            return None
        k, grp = kind
        bad = ((k == "melee" and grp not in rules["melee"]) or (k == "thrown" and grp not in rules["thrown"])
               or (k == "ranged" and (rules["ranged"] == "none" or (rules["ranged"] == "no_heavy" and grp == "heavy"))))
    elif cat == "Zbroj":
        known = {a[0] for a in ARMORS}
        bad = name in known and rules["armor"] != "all" and name not in rules["armor"]
    elif cat == "Štít":
        bad = not rules["shield"]
    else:
        return None
    return f"{cls} neovládá: {name} (ovládá {CLASS_GEAR_TEXT[cls]})." if bad else None
