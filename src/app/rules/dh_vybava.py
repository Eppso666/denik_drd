"""Katalog výzbroje a výstroje Dračí Hlídky (Příručka pro hráče, kapitola Výzbroj a výstroj).

Hmotnost je v librách (1 lb ≈ 1 kg). Ceny jsou podle pravidel orientační.
Zbraně: útočnost, zranění, obrana zbraně; skupina udává potřebnou opravu za Sílu
(lehké bez omezení, střední SIL 0+, těžké SIL +2).
"""
from __future__ import annotations

SIL_REQ = {"lehká": None, "střední": 0, "těžká": 2}

# (název, typ, útočnost, zranění, obrana, hmotnost lb, cena, skupina)
UNARMED = [("Okované rukavice", "drtivá", 0, 1, 1, 0.3, "1 zl", "lehká")]
MELEE_1H = [
    ("Nůž", "bodná/vrhací", 1, 1, 0, 0.4, "5 st", "lehká"),
    ("Dýka", "bodná/vrhací", 2, 1, 1, 0.5, "1 zl", "lehká"),
    ("Tesák", "sečná", 3, 2, 1, 0.8, "2 zl", "lehká"),
    ("Krátký meč", "sečná/bodná", 4, 1, 2, 0.9, "12 zl", "lehká"),
    ("Kord", "bodná", 5, 0, 2, 0.8, "24 zl", "lehká"),
    ("Pochodeň", "drtivá", 3, 0, 1, 0.5, "7 md", "lehká"),
    ("Obušek", "drtivá", 3, 3, 1, 0.9, "1 st", "lehká"),
    ("Šavle", "sečná", 4, 2, 2, 1.1, "30 zl", "střední"),
    ("Široký meč", "sečná/bodná", 5, 1, 2, 1.2, "20 zl", "střední"),
    ("Sekera", "sečná/vrhací", 4, 3, 1, 1.3, "5 zl", "střední"),
    ("Rapír", "sečná/bodná", 6, 0, 2, 1.3, "35 zl", "střední"),
    ("Oštěp", "bodná/vrhací", 6, 0, 1, 1.1, "8 st", "střední"),
    ("Meč bastard", "sečná/bodná", 6, 1, 2, 1.5, "30 zl", "těžká"),
    ("Kyj", "drtivá", 5, 3, 0, 1.7, "3 zl", "těžká"),
    ("Palcát", "drtivá", 5, 3, 1, 1.6, "15 zl", "těžká"),
    ("Válečné kladivo", "drtivá", 5, 3, 1, 1.5, "10 zl", "těžká"),
    ("Řemdih", "drtivá", 6, 3, 0, 1.5, "8 zl", "těžká"),
]
MELEE_2H = [
    ("Dřevěná hůl", "drtivá", 5, 0, 1, 1.0, "2 st", "lehká"),
    ("Okovaná hůl", "drtivá", 6, 1, 1, 1.3, "5 st", "lehká"),
    ("Kosa", "sečná", 6, 0, 0, 1.2, "1 zl", "lehká"),
    ("Kopí", "bodná", 6, 2, 1, 1.7, "3 zl", "střední"),
    ("Vidle", "bodná", 4, 2, 1, 2.0, "1 zl", "střední"),
    ("Sudlice", "sečná", 6, 3, 1, 2.1, "5 zl", "střední"),
    ("Dlouhý meč", "sečná/bodná", 7, 0, 2, 1.6, "40 zl", "střední"),
    ("Okovaný cep", "drtivá", 4, 3, 0, 3.3, "2 zl", "těžká"),
    ("Halapartna", "sečná", 8, 0, 1, 2.4, "12 zl", "těžká"),
    ("Obouruční kladivo", "drtivá", 7, 4, 0, 4.0, "20 zl", "těžká"),
    ("Obouruční meč", "sečná", 8, 1, 2, 2.3, "60 zl", "těžká"),
    ("Těžký kyj", "drtivá", 7, 3, 0, 4.5, "5 zl", "těžká"),
    ("Obouruční sekera", "sečná", 7, 3, 1, 3.0, "25 zl", "těžká"),
    ("Trojzubec", "bodná", 8, 0, 1, 2.2, "9 zl", "těžká"),
    ("Obouruční řemdih", "drtivá", 6, 5, 0, 3.0, "15 zl", "těžká"),
]
# (název, typ, útočnost, zranění, obrana, dostřel, hmotnost lb, cena, skupina)
RANGED = [
    ("Hvězdice", "vrhací", 3, 1, 0, "6/15", 0.1, "1 st", "lehká"),
    ("Flakón (vrhací)", "vrhací", 0, 0, 0, "6/15", 0.2, "1 st", "lehká"),
    ("Kámen", "vrhací", 0, 1, 0, "6/15", 0.2, "–", "lehká"),
    ("Vrhací nůž", "vrhací", 1, 1, 0, "6/15", 0.4, "5 st", "lehká"),
    ("Vrhací dýka", "vrhací", 2, 1, 1, "6/15", 0.5, "1 zl", "lehká"),
    ("Prak", "střelná", 3, 0, 0, "40/100", 0.2, "1 st", "lehká"),
    ("Krátký luk", "střelná", 4, 0, 0, "60/180", 0.5, "3 zl", "lehká"),
    ("Lehká kuše", "střelná", 4, 1, 1, "40/150", 3.5, "7 zl", "lehká"),
    ("Lovecká kuše", "střelná", 5, 2, 1, "60/80", 4.0, "10 zl", "střední"),
    ("Lovecký luk", "střelná", 5, 2, 0, "100/230", 0.7, "7 zl", "střední"),
    ("Vrhací sekera", "vrhací", 4, 3, 1, "6/15", 1.3, "5 zl", "střední"),
    ("Vrhací oštěp", "vrhací", 6, 0, 1, "15/30", 1.1, "8 st", "střední"),
    ("Těžká kuše", "střelná", 8, 7, 1, "100/350", 5.5, "30 zl", "těžká"),
    ("Dlouhý luk", "střelná", 7, 3, 0, "150/350", 1.0, "10 zl", "těžká"),
]
# Zbroje: (název, kvalita, hmotnost A/B/C lb, cena A/B/C zl, skupina)
ARMORS = [
    ("Vycpávaná zbroj", 1, (0.5, 0.7, 1.0), (3, 5, 7), "lehká"),
    ("Prošívaná zbroj", 2, (1.2, 1.8, 2.4), (10, 15, 25), "lehká"),
    ("Kožená zbroj", 3, (3, 3.5, 4.3), (30, 40, 50), "střední"),
    ("Kroužková zbroj", 4, (10, 15, 20), (60, 80, 95), "střední"),
    ("Šupinová zbroj", 5, (12, 17, 23), (135, 150, 165), "střední"),
    ("Plátová zbroj", 6, (15, 20, 25), (215, 225, 245), "těžká"),
    ("Rytířská zbroj", 7, (20, 30, 40), (330, 350, 370), "těžká"),
]
# Štíty: (název, kvalita, hmotnost lb, cena, skupina, poznámka)
SHIELDS = [
    ("Puklíř", 1, 1, "5 zl", "lehká", ""),
    ("Dřevěný štít", 2, 3, "10 zl", "střední", ""),
    ("Železný štít", 3, 5, "15 zl", "těžká", ""),
    ("Pavéza", 6, 15, "30 zl", "těžká", "nosí se oběma rukama"),
]
# Doplňky ke zbraním a základní vybavení: (název, cena, hmotnost lb, poznámka)
GEAR = [
    ("Pochva na meč", "1 zl", 0.25, ""),
    ("Pouzdro na nůž / dýku", "3 st", 0.1, ""),
    ("Toulec na šípy / šipky", "1 zl", 0.25, "na 20 střel"),
    ("Šíp (obyčejný)", "1 st", 0.03, ""),
    ("Šíp (zápalný)", "3 st", 0.04, ""),
    ("Šíp (stříbrný)", "5 st", 0.03, ""),
    ("Šipka (obyčejná)", "1 st", 0.03, "do kuše"),
    ("Šipka (zápalná)", "3 st", 0.04, "do kuše"),
    ("Šipka (stříbrná)", "5 st", 0.03, "do kuše"),
    ("Alchymistická truhla (základní)", "10 zl", 2, "30 × 20 × 20 coulů"),
    ("Cestovní šaty", "2 zl", 2, "kalhoty, opasek, tunika, plášť, boty"),
    ("Deka", "5 st", 1, ""),
    ("Flakón", "1 st", 0.2, "0,2 litru"),
    ("Herecké rekvizity", "2 zl", 2, "líčidla a dva kostýmy"),
    ("Jehla a nit", "4 md", 0, ""),
    ("Kotlík", "1 zl", 2, "měděný"),
    ("Kožená torna", "7 st", 0.5, "unese 5 lb"),
    ("Kotvička", "7 st", 1, ""),
    ("Křesadlo", "1 st", 0.2, ""),
    ("Křída", "1 md", 0, ""),
    ("Láhev oleje", "5 st", 1, "do lucerny na 4 hodiny"),
    ("Lano (10 sáhů)", "2 zl", 3, ""),
    ("Lucerna", "6 st", 0.7, "světlo do 10 sáhů"),
    ("Měch na vodu", "5 st", 0.5, "1,5 l, hmotnost prázdného"),
    ("Měšec", "2 st", 0.1, "až 100 mincí"),
    ("Obvazy", "7 md", 0, ""),
    ("Páčidlo", "7 st", 1, ""),
    ("Padělatelské vybavení", "3 zl", 0.5, ""),
    ("Pergamen", "4 st", 0, ""),
    ("Pochodeň (světlo)", "7 md", 0.5, "hoří 2 směny, světlo 10 sáhů"),
    ("Psací potřeby", "2 st", 0.3, "brk a inkoust"),
    ("Svěcená voda", "2 st", 0.4, "proti nemrtvým a neviděným"),
    ("Velký vak", "4 st", 0.2, "unese 20 lb"),
    ("Vlčí mor", "1 md", 0, "proti lykantropům"),
    ("Zlodějské vybavení", "5 zl", 5, "kotvička, lano, paklíče, vrták, drátek"),
    ("Zrcátko", "2 st", 0, ""),
    ("Železná zásoba", "1 zl", 3, "jídlo na 7 dní"),
]

RACE_SIZE = {"Člověk": "B", "Trpaslík": "A", "Elf": "B", "Barbar": "B", "Obr": "C", "Gnóm": "A", "Půlčík": "A"}

# Tabulka nosnosti: oprava za SIL -> základní nosnost (lb)
CAPACITY = {-5: 7, -4: 8, -3: 9, -2: 11, -1: 13, 0: 15, 1: 17, 2: 19, 3: 21, 4: 23, 5: 25, 6: 28}


def carry_capacity(sil_bonus: int) -> int:
    b = max(-5, min(6, int(sil_bonus)))
    return CAPACITY[b]


def _req(grp: str) -> str:
    r = SIL_REQ.get(grp)
    return grp if r is None else f"{grp} (SIL {'+' if r > 0 else ''}{r} a víc)"


def catalog(race: str | None = None) -> list[dict]:
    size = RACE_SIZE.get(race or "", "B")
    si = "ABC".index(size)
    out: list[dict] = []
    for rows, hands in ((UNARMED, "beze zbraně"), (MELEE_1H, "jednoruční"), (MELEE_2H, "obouruční")):
        for name, typ, att, dmg, dfn, lb, price, grp in rows:
            out.append({"group": "Zbraně na blízko", "name": name, "category": "Zbraň", "attack": att,
                        "damage": dmg, "defense": dfn, "ranged": False, "weight": lb, "price": price,
                        "info": f"{hands} · {typ} · {_req(grp)}"})
    for name, typ, att, dmg, dfn, rng, lb, price, grp in RANGED:
        out.append({"group": "Střelné a vrhací", "name": name, "category": "Zbraň", "attack": att, "damage": dmg,
                    "defense": dfn, "ranged": True, "weight": lb, "price": price,
                    "info": f"{typ} · dostřel {rng} sáhů · {_req(grp)}"})
    for name, q, weights, prices, grp in ARMORS:
        out.append({"group": "Zbroje a štíty", "name": name, "category": "Zbroj", "quality": q,
                    "weight": weights[si], "price": f"{prices[si]} zl",
                    "info": f"kvalita +{q} · {_req(grp)} · velikost {size}"})
    for name, q, lb, price, grp, note in SHIELDS:
        out.append({"group": "Zbroje a štíty", "name": name, "category": "Štít", "defense": q, "weight": lb,
                    "price": price, "info": f"kvalita +{q} · {_req(grp)}" + (f" · {note}" if note else "")})
    for name, price, lb, note in GEAR:
        out.append({"group": "Výstroj", "name": name, "category": "Ostatní", "weight": lb, "price": price,
                    "info": note})
    return out
