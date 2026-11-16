"""Alchymistické předměty DrD 1.6 – Pravidla pro začátečníky str. 46–53.

Magenergie (magy) a suroviny (zlaťáky) se při výrobě odečtou ze zásob v truhle – i při neúspěchu.
Trvalé předměty s démonem astrální sféry umí vyrobit jen alchymista, který ovládá vyvolání démona dané sféry
(Pravidla pro pokročilé, theurg) – deník je nezakazuje, jen upozorní.
"""
from __future__ import annotations

# (název, magenergie, magů (číslo), suroviny zl, základ, trvání, výroba, sféra, stručně)
_ITEMS = {
    "Lektvary": [
        ("Antigravitační cloumák", "10 magů", 10, 25, "medovina", "1 směna", "2 směny", None,
         "Volný pohyb jako ve stavu beztíže."),
        ("Čarovná rtuť", "4 magy", 4, 20, "rtuť (4 zl)", "1 úspěšné použití", "1 směna", None,
         "Kulička se kutálí k pokladu do 5 sáhů."),
        ("Éterický olej", "7 magů", 7, 33, "olej", "1–2 směny", "3 směny", None,
         "Postava zprůsvitní a projde stěnou."),
        ("Lektvar chladných vod", "5 magů", 5, 12, "voda", "3 směny", "1 směna", None,
         "Silný oheň zraní jen napůl, obyčejný vůbec."),
        ("Lektvar mlhovina", "5 magů", 5, 11, "kravské mléko", "4 směny", "3 kola", None,
         "Postava se promění v oblak mlhy."),
        ("Lektvar obří síly", "25 magů", 25, 35, "červené nebo bílé víno", "1 směna", "2 kola", None,
         "Síla +5 (nejvýš 21)."),
        ("Lektvar rudého kříže", "5 magů", 5, 10, "červené víno", "ihned", "1 směna", None,
         "Vyléčí 3–8 životů (1k6+2)."),
        ("Lektvar vlády nad lykantropy", "8 magů", 8, 21, "voda", "1–3 směny", "2 směny", None,
         "Lykantrop jedná jako zmámený."),
        ("Lektvar zmenšování", "4 magy", 4, 12, "voda", "6 směn", "1 směna", None,
         "Zmenší postavu o dvě třídy velikosti."),
        ("Megacloumák", "4 magy", 4, 11, "ocet", "ihned", "1 směna", None, "Odstraní mdloby (vdechnutí)."),
        ("Metamorfóza", "13 magů", 13, 50, "koňská moč", "3 směny", "4 směny", None,
         "Proměna v živou bytost do 8 sáhů."),
        ("Pavoučí lektvar", "3 magy", 3, 15, "pivo", "2 směny", "1 směna", None, "Pohyb po stěnách."),
        ("Rychlost", "9 magů", 9, 29, "voda", "5 kol", "3 kola", None, "Dvojnásobná rychlost."),
    ],
    "Svitky": [
        ("Ochrana před ďábly", "50 magů", 50, 75, "pergamen", "2 směny", "1 den; doma", None,
         "Bariéra proti ďáblům."),
        ("Ochrana před nemrtvými", "6 magů", 6, 20, "pergamen", "4 směny", "10 kol", None,
         "Nemrtvý projde jen přes past Roz – 10."),
        ("Ochrana před neviděnými", "8 magů", 8, 40, "pergamen", "3 směny", "1 směna", None,
         "Neviděný projde jen přes past Roz – 8."),
        ("Ochrana před démony", "10 magů", 10, 60, "pergamen", "4 směny", "1 den; doma", None,
         "Chrání alchymistu při vyvolávání démonů."),
        ("Ochrana před kouzly", "podle úvahy alchymisty", None, 19, "pergamen", "3 směny", "10 kol", None,
         "Kouzla bariérou selžou s pravděpodobností magy svitku / magy kouzla × 100 %."),
    ],
    "Pomůcky": [
        ("Detekční hůlka", "40 magů", 40, 170, "dřevo (1 mn)", "12 kol vyhledávání", "4 dny; doma", None,
         "Najde tajné dveře a skryté východy."),
        ("Lakmusový papírek", "2 magy", 2, 5, "pergamen (1/10 svitku)", "1 použití", "1 směna", None,
         "Určí složení kapaliny, jed i lektvar."),
        ("Píšťalka", "30 magů", 30, 25, "vrbový proutek", "8 otevření", "4 dny; doma", None,
         "Otevírá nemagické zámky (3 kola, 3 magy)."),
    ],
    "Trvalé předměty": [
        ("Čarovné brnění", "90 magů", 90, 30, "kožené brnění", "1 rok", "1 týden; doma", 2,
         "Kvalita zbroje o 1 vyšší."),
        ("Kouzelný luk", "30 magů", 30, 120, "dlouhý luk", "1 rok a 6 měsíců", "1 týden; doma", 1,
         "Dlouhý luk se silou zbraně 6."),
        ("Kouzelný štít", "95 magů", 95, 30, "štít", "1 rok", "1 den; doma", 2, "Štít s KZ +2."),
        ("Meč noci", "185 magů", 185, 75, "široký meč", "1 rok", "1 týden; doma", 4,
         "SZ 13 proti nemrtvým, jinak 7."),
        ("Ohnivý meč", "80 magů", 80, 80, "dlouhý meč", "1 rok", "1 týden; doma", 2,
         "Denně 4 magy na kouzla oheň a světlo."),
        ("Plášť", "80 magů", 80, 10, "elfí plátno (20 mn / 10 zl)", "2 roky", "2 dny; doma", 2,
         "Kvalita zbroje o 1 vyšší."),
        ("Prsten černé vodoměrky", "95 magů", 95, 200, "stříbro (1 zl)", "2 roky", "3 dny; doma", 2,
         "Viz pravidla str. 51."),
        ("Prsten knížete D'Raguly", "70 magů", 70, 426, "železo", "2 roky", "6 dní; doma", 2,
         "Pomáhá v boji – viz pravidla str. 51."),
        ("Prsten uhranutí", "280 magů", 280, 100, "platina a olivíny (100 zl)", "2 roky", "7 dní; doma", 6,
         "Vlastní magenergie na psychická kouzla."),
        ("Sluneční prsten", "225 magů", 225, 100, "zlato a rubín (150 zl)", "2 roky", "5 dní; doma", 5,
         "Vlastní magická síla – viz pravidla."),
        ("Ebenová hůlka", "75 magů", 75, 80, "eben (2 mn / 50 zl)", "10 let", "1 týden; doma", 2,
         "Chrání před některými magickými útoky."),
        ("Elfí boty", "20 magů", 20, 80, "boty z rysí kůže (10 mn / 8 zl)", "10 let", "3 dny; doma", 1,
         "Zloděj se pohybuje tiše jako o 2 úrovně výš."),
        ("Kostka štěstí", "7 magů", 7, 80, "kámen", "10 let", "1 týden; doma", 1, "Hod kostkou ovlivní štěstí."),
        ("Létající koště", "92 magů", 92, 10, "koště (20 mn / 1 st)", "2 roky", "2 dny; doma", 2,
         "Let 80 sáhů za kolo do 980 mincí zátěže."),
        ("Pytel beztíže", "40 magů", 40, 150, "velký pytel", "1 rok", "2 dny; doma", 2,
         "Uveze až 1000 mn bez váhy."),
    ],
    "Jedy": [
        ("Černá zhouba", "žádná", 0, 48, "olej", "ihned / 5 kol", "5 směn", None,
         "Nebezpečnost 5, ochromení na 1–3 / 3–8 směn (požití)."),
        ("Jablečná vůně", "žádná", 0, 70, "mošt", "ihned / 1 kolo", "24 směn; doma", None,
         "Nebezpečnost 7, zranění –/2–7 (vdechnutí)."),
        ("Kurare", "žádná", 0, 100, "borůvková šťáva", "ihned / 1 kolo", "1 den; doma", None,
         "Nebezpečnost 4, zranění –/10–100 (krev)."),
        ("Melenova pomsta", "1 mag", 1, 60, "voda", "ihned / 1 směna", "10 směn", None,
         "Nebezpečnost 7, zranění 1–6 / 2–12 (požití)."),
    ],
    "Nemagické": [
        ("Bomba", "žádná", 0, 65, "železná koule, dřevo (200 mn / 5 zl)", "ihned", "4 hodiny; doma", None,
         "Výbušná koule s doutnákem."),
        ("Ohnivá hlína", "žádná", 0, 20, "hlína (10 mn)", "ihned", "8 kol", None, "Vrhací výbušné koule."),
        ("Hvězdice-bumerang", "5 magů", 5, 10, "hvězdice", "stále", "1 den; doma", None,
         "Při minutí se vrátí majiteli."),
        ("Zubaté ostří", "1 mag", 1, 10, "dýka", "stále", "1 den; doma", None, "Dýka: SZ 1, útočnost 3."),
    ],
}

FIELDS = ("name", "mana", "mags", "raw", "base", "duration", "make", "sphere", "desc")
ITEMS: list[dict] = [dict(zip(FIELDS, it), group=g) for g, rows in _ITEMS.items() for it in rows]
ITEM_BY_NAME = {i["name"]: i for i in ITEMS}
GROUPS = list(_ITEMS)

# Pravděpodobnost úspěchu alchymisty podle obratnosti
SUCCESS = [(9, 32), (12, 47), (14, 61), (16, 74), (18, 85), (20, 95), (99, 99)]


def success_chance(obr: int) -> int:
    for top, pct in SUCCESS:
        if obr <= top:
            return pct
    return 99


def craft_problem(c: dict, item: dict) -> str | None:
    """Proč předmět teď nejde vyrobit (nedostatek magenergie nebo surovin)."""
    if item["mags"] and item["mags"] > int(c.get("mana", 0)):
        return f"chybí magenergie ({c.get('mana', 0)}/{item['mags']} magů)"
    if item["raw"] > int(c.get("raw", 0)):
        return f"chybí suroviny ({c.get('raw', 0)}/{item['raw']} zl)"
    return None


def sphere_note(item: dict) -> str | None:
    if item["sphere"]:
        return f"démon {item['sphere']}. sféry – jen pokud ho alchymista umí vyvolat (PJ)"
    return None
