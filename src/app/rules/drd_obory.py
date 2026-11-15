"""Obory povolání DrD 1.6 od 6. úrovně (Pravidla pro pokročilé), psi hraničáře a přátelé kouzelníka.

Názvy schopností, úrovně a čísla odpovídají pravidlům, popisy jsou stručná připomenutí vlastními slovy.
"""
from __future__ import annotations

ADV_LEVEL = 6  # od této úrovně si postava volí obor

# povolání -> [(obor, krátký popis, [(schopnost, od úrovně, stručně)])]
BRANCHES: dict[str, list[tuple[str, str, list[tuple[str, int, str]]]]] = {
    "Válečník": [
        ("Bojovník", "Spoléhá na hrubou sílu a těžké, obvykle obouruční zbraně.", [
            ("Sehranost v útoku i obraně", 6, "bonus podle počtu společných výcviků (Tabulka sehranosti)"),
            ("Zastrašení skupiny", 6, "až 3 sousední nepřátelé; od 12. úr. skupina do 10 sáhů"),
            ("Iniciativa s těžkými zbraněmi", 6, "neztrácí iniciativu s žádnou zbraní tváří v tvář"),
            ("Výpad a kryt", 6, "+1/−2; od 12. úr. také +2/−4"),
            ("Drtivost", 6, "+1 k útočnosti proti velikosti A0–B; od 10. úr. +2"),
            ("Průraznost", 6, "+1 k ÚČ proti velikosti C–E; od 10. úr. +2"),
            ("Změna v berserkra", 6, "past na Int podle situace; od 10. úr. částečně ovladatelná"),
            ("Odhad soupeře", 8, "útočnost nestvůry; od 10. úr. dva údaje, od 12. úr. i životaschopnost"),
            ("Hrubá síla", 8, "+1 k bonusu za Sil při hodu proti pasti; od 15. úr. +2"),
            ("Vícenásobné útoky", 10, "obouruční zbraní 2× za kolo; od 12. úr. střelba 3× za 2 kola; "
                                      "od 15. úr. i jednoruční"),
            ("Chladnokrevnost", 13, "+1 proti psychickým a iluzím"),
        ]),
        ("Šermíř", "Bojuje technikou a rychlostí, mečem či podobnou zbraní.", [
            ("Sehranost v útoku i obraně", 6, "bonus podle počtu společných výcviků (Tabulka sehranosti)"),
            ("Výpad a kryt", 6, "+1/−2; od 11. úr. také +2/−4"),
            ("Šerm", 6, "+1 k ÚČ i OČ proti humanoidovi s mečem; od 10. úr. +2"),
            ("Útok z obrany", 6, "po minutí soupeř ztrácí rozdíl hodů (1. útok v kole)"),
            ("Cvik", 6, "po 5 úrovních se stejným typem zbraně +1 k útočnosti"),
            ("Vícenásobné útoky", 8, "jednoruční 2× za kolo; od 10. úr. střelba 3× za 2 kola; "
                                     "od 13. úr. 5× za 2 kola"),
            ("Odhad soupeře", 10, "útočnost nestvůry; od 12. úr. dva údaje, od 15. úr. životaschopnost"),
        ]),
    ],
    "Hraničář": [
        ("Druid", "Lesní čaroděj, čerpá sílu z hvozdu a zvířat.", [
            ("Rozšířená léčivá kouzla", 6, "léčení i na obratlovce; od 12. úr. i na běžné tvory"),
            ("Boj se zvířaty", 6, "+2 proti zvířatům s Int 1; od 10. úr. +3, od 14. úr. +4"),
            ("Nepřirozené chování zvířat", 6, "pozná zvíře pod vlivem kouzla"),
            ("Odvracení zvířat", 6, "2k6 podle Tabulky odvracení zvířat"),
            ("Druidova hůl", 6, "SZ 7/−2, obrana +2; od 10. úr. 3 útoky za 2 kola"),
            ("Předpovídání počasí", 6, "60 % + úroveň + oprava Int na příští den"),
            ("Lesní kouzla", 6, "cit dřeva, kamene, vody, země, hněv a láska lesa, pouta, temnota…"),
            ("Pomocná lesní kouzla", 6, "přání, prosba, stesk, nářek"),
            ("Kratší vyvolávání kouzel", 13, "doba vyvolání o třetinu kratší"),
        ]),
        ("Chodec", "Poutník a bojovník s kouzelným mečem.", [
            ("Rozšířená léčivá kouzla", 6, "léčení i na obratlovce; od 12. úr. i na běžné tvory"),
            ("Kouzla pocestných", 6, "ochrana před bouří, deštěm, vlky a zimou, přivolej druida, rozdělej oheň"),
            ("Chodcův meč", 6, "kouzelný meč s vlastními kouzly (dvojitý sek, odraz šípy…)"),
            ("Psychická kouzla", 6, "odhal vinu, odveď pozornost, uhrančivý pohled, uspi okolí…"),
            ("Odhad přesvědčení", 6, "podle Tabulky odhadu přesvědčení"),
            ("Rychlý pochod", 6, "24 h dvojnásobným pochodem bez vlivu únavy"),
            ("Hbitost v obraně", 6, "+1 k hodu na obranu"),
            ("Výpad a kryt", 6, "soustředění na útok nebo obranu"),
            ("Ochočování nestvůr", 6, "+1; od 12. úr. +2"),
            ("Rychlá střelba", 7, "z luku 3× za 2 kola; od 12. úr. 2× za kolo"),
            ("Druhá mimosmyslová schopnost", 12, "podle vlastní volby"),
        ]),
    ],
    "Alchymista": [
        ("Theurg", "Zkoumá astrální síly, vyvolává elementály a démony.", [
            ("Vyvolávání elementálů", 6, "gnóm, undina, sylfa, salamandr – přes elementální hůl"),
            ("Elementální hůl", 6, "nástroj pro vyvolání elementálů"),
            ("Styk s astrálními sférami", 6, "otázky a pomoc sfér podle Tabulky astrálních sfér"),
            ("Zaklínání démonů do předmětů", 6, "démoni s různými schopnostmi v kouzelných předmětech"),
            ("Poznávání kouzelných předmětů", 6, "pozná vlastnosti kouzelného předmětu"),
            ("Léčivé a Welfovy lektvary", 6, "nové lektvary společné pro alchymistu"),
        ]),
        ("Pyrofor", "Bojový alchymista – rachejtle, pasti, jedy.", [
            ("Rachejtle", 6, "obyčejné, vějířové a naváděné"),
            ("Odhad životnosti trhavin", 6, "pozná, kdy výrobek vybuchne či zvlhne"),
            ("Líčení pastí", 6, "šipkové, plynové a výbušné pasti"),
            ("Jedy a protijedy", 6, "výroba jedů a protijedů"),
            ("Léčivé a Welfovy lektvary", 6, "nové lektvary společné pro alchymistu"),
            ("Silnější jedy", 10, "od 10. úrovně další druhy jedů"),
        ]),
    ],
    "Kouzelník": [
        ("Mág", "Studuje magii mysli: podrobování a mentální souboj.", [
            ("Posílení psychických kouzel", 6, "nebezpečnost pasti o 1 vyšší u psychických kouzel"),
            ("Odolnost proti psychickým kouzlům", 6, "+1 k hodu proti pasti"),
            ("Omezení kouzel", 6, "přímo jen vybraná kouzla, ostatní přes dvířka, dveře, bránu"),
            ("Pomocná kouzla", 6, "dvířka, dveře, brána"),
            ("Podrobování", 6, "převzetí cizího těla podle síly mysli"),
            ("Mentální souboj", 6, "SUM/SMO = ZSM + úroveň + oprava Chr"),
            ("Iniciativa v kouzlení", 6, "+2 k iniciativě; od 11. úr. +3"),
            ("Kratší vyvolávání kouzel", 11, "doba vyvolání o třetinu kratší"),
        ]),
        ("Čaroděj", "Praktická magie bez omezení výběru kouzel.", [
            ("Neomezený výběr kouzel", 6, "všechna kouzla PPZ i PPP"),
            ("Silnější přátelé", 6, "lepší kočka, havran a ďáblík (Tabulka čarodějových přátel)"),
            ("Iniciativa v kouzlení", 6, "+2 k iniciativě; od 11. úr. +3"),
            ("Kratší vyvolávání kouzel", 11, "doba vyvolání o třetinu kratší"),
        ]),
    ],
    "Zloděj": [
        ("Lupič", "Praktický zloděj – zámky, pasti, poklady.", [
            ("Střelba ze zálohy", 6, "dvojnásobný rozdíl hodů střelnou nebo vrhací zbraní"),
            ("Vrh", 6, "bonus a iniciativa s vrhací zbraní"),
            ("Výpad a kryt", 6, "soustředění na útok nebo obranu"),
            ("Nenápadnost", 6, "k% podle tabulky a místa (Tabulka nenápadnosti)"),
            ("Křišťálový klíč", 6, "otevírá i magické zámky"),
            ("Nastražení pasti v zámku", 6, "jednorázová past v zámku"),
            ("Určení hodnoty pokladů", 6, "odhad ceny a odhalení padělků"),
            ("Boj beze zbraně", 6, "v obraně i v útoku, citlivá místa"),
        ]),
        ("Sicco", "Muž intrik a temných uliček.", [
            ("Střelba ze zálohy", 6, "dvojnásobný rozdíl hodů střelnou nebo vrhací zbraní"),
            ("Vrh", 6, "bonus a iniciativa s vrhací zbraní"),
            ("Zabití", 6, "tiché zabití nic netušící oběti"),
            ("Boj s dýkou", 6, "zvláštní bonusy s dýkou"),
            ("Odhad lidí", 6, "k% podle Tabulky zvláštních schopností sicca"),
            ("Síť", 6, "výkonná, výzvědná a ochranná síť informátorů"),
        ]),
    ],
}

BRANCH_TO_CLASS = {b[0]: cls for cls, bl in BRANCHES.items() for b in bl}

# Zlodějské schopnosti 6.–15. úrovně: (název, [úr. 6..15], [(vlastnost, násobek)])
LUPIC_TABLE = [
    ("Převleky", [28, 32, 37, 41, 47, 49, 52, 55, 57, 60], [("CHA", 3)]),
    ("Získání důvěry", [25, 28, 30, 33, 38, 42, 48, 53, 59, 65], [("CHA", 3)]),
    ("Objevení mechanismu", [35, 40, 45, 50, 55, 60, 65, 70, 75, 80], [("OBR", 2)]),
    ("Objevení objektu", [40, 45, 50, 55, 60, 65, 70, 75, 80, 85], [("OBR", 3)]),
    ("Zneškodnění mechanismu", [40, 45, 50, 55, 60, 65, 70, 75, 80, 85], [("OBR", 2)]),
    ("Otevření objektu", [50, 54, 58, 61, 65, 69, 74, 78, 82, 86], [("OBR", 3)]),
    ("Šplhání po zdech", [80, 85, 90, 95, 100, 102, 104, 106, 108, 110], [("OBR", 1)]),
    ("Skok z výšky", [80, 83, 86, 89, 92, 95, 98, 101, 104, 107], [("OBR", 1)]),
    ("Tichý pohyb", [29, 32, 35, 37, 40, 42, 45, 48, 50, 53], [("OBR", 1)]),
    ("Schování se ve stínu", [52, 55, 58, 60, 62, 65, 67, 70, 72, 75], [("OBR", 1)]),
    ("Vybírání kapes", [26, 30, 35, 39, 45, 52, 60, 68, 75, 85], [("CHA", 1), ("OBR", 1)]),
    ("Nenápadnost", [20, 22, 25, 27, 30, 32, 35, 37, 40, 42], [("CHA", 2)]),
]
SICCO_TABLE = [
    ("Převleky", [33, 39, 46, 53, 60, 68, 75, 83, 90, 95], [("CHA", 3)]),
    ("Získání důvěry", [28, 33, 39, 45, 51, 55, 60, 66, 72, 80], [("CHA", 3)]),
    ("Objevení mechanismu", [34, 38, 42, 46, 50, 54, 58, 62, 66, 70], [("OBR", 2)]),
    ("Objevení objektu", [39, 43, 47, 50, 54, 59, 63, 66, 70, 74], [("OBR", 3)]),
    ("Zneškodnění mechanismu", [39, 43, 47, 50, 54, 59, 63, 66, 70, 74], [("OBR", 2)]),
    ("Otevření objektu", [48, 52, 55, 58, 63, 67, 70, 73, 76, 80], [("OBR", 3)]),
    ("Šplhání po zdech", [80, 82, 83, 85, 86, 88, 90, 91, 93, 95], [("OBR", 1)]),
    ("Skok z výšky", [79, 81, 83, 85, 87, 89, 91, 93, 95, 97], [("OBR", 1)]),
    ("Tichý pohyb", [29, 32, 35, 37, 40, 42, 45, 48, 50, 53], [("OBR", 1)]),
    ("Schování se ve stínu", [52, 55, 58, 60, 62, 65, 67, 70, 72, 75], [("OBR", 2)]),
    ("Vybírání kapes", [23, 25, 27, 29, 32, 35, 38, 42, 45, 49], [("CHA", 1), ("OBR", 1)]),
    ("Odhad lidí", [20, 23, 25, 27, 30, 33, 35, 38, 40, 43], []),
]

# --- pomocníci -------------------------------------------------------------------------------

STAT_LABELS = ["Životaschopnost", "Útočné číslo", "Obranné číslo", "Odolnost", "Velikost", "Bojovnost",
               "Zranitelnost", "Pohyblivost", "Vytrvalost", "Inteligence", "Charisma", "Magenergie",
               "Počet kouzel", "Váha", "Zkušenost"]

# Psi hraničáře (PPZ): k% při hodu, statistiky. „adv“ = pes, kterého má hraničář aspoň 5 úrovní (PPP).
DOGS = [
    {"name": "Pes hlídací", "roll": (1, 20),
     "special": "Ucítí bytost do 15 sáhů (spící do 10 sáhů) a upozorní pána.",
     "base": {"Životaschopnost": "1", "Útočné číslo": "(+1 + 3) = 4, tlama", "Obranné číslo": "(0 + 2) = 2",
              "Odolnost": "9", "Velikost": "A, zřídka B", "Bojovnost": "6", "Zranitelnost": "zvíře",
              "Pohyblivost": "14/šelma", "Vytrvalost": "13/šelma", "Inteligence": "1", "Zkušenost": "10"},
     "adv": {"Životaschopnost": "2", "Útočné číslo": "(+2 + 3) = 5, tlama", "Obranné číslo": "(+1 + 2) = 3",
             "Odolnost": "10", "Velikost": "A, zřídka B", "Bojovnost": "7", "Zranitelnost": "zvíře",
             "Pohyblivost": "14/šelma", "Vytrvalost": "13/šelma", "Inteligence": "1", "Zkušenost": "20"}},
    {"name": "Pes lovecký", "roll": (21, 34),
     "special": "Stopování +15 % ve volné přírodě, +8 % v uzavřených prostorách.",
     "base": {"Životaschopnost": "2", "Útočné číslo": "(+1 + 3) = 4, tlama", "Obranné číslo": "(+1 + 2) = 3",
              "Odolnost": "10", "Velikost": "A nebo B", "Bojovnost": "7", "Zranitelnost": "zvíře",
              "Pohyblivost": "15/šelma", "Vytrvalost": "14/šelma", "Inteligence": "1", "Zkušenost": "20"},
     "adv": {"Životaschopnost": "3", "Útočné číslo": "(+2 + 3) = 5, tlama", "Obranné číslo": "(+2 + 2) = 4",
             "Odolnost": "11", "Velikost": "A–B", "Bojovnost": "8", "Zranitelnost": "zvíře",
             "Pohyblivost": "15/šelma", "Vytrvalost": "14/šelma", "Inteligence": "1", "Zkušenost": "35"}},
    {"name": "Pes válečný", "roll": (35, 40),
     "special": "Rozšířený souboj +1 k iniciativě; v základním souboji každé druhé kolo iniciativa.",
     "base": {"Životaschopnost": "3", "Útočné číslo": "(+2 + 3) = 5, tlama", "Obranné číslo": "(+3 + 2) = 5",
              "Odolnost": "11", "Velikost": "B", "Bojovnost": "8", "Zranitelnost": "zvíře",
              "Pohyblivost": "16/šelma", "Vytrvalost": "15/šelma", "Inteligence": "1", "Zkušenost": "45"},
     "adv": {"Životaschopnost": "4", "Útočné číslo": "(+3 + 3) = 6, tlama", "Obranné číslo": "(+4 + 2) = 6",
             "Odolnost": "12", "Velikost": "B", "Bojovnost": "9", "Zranitelnost": "zvíře",
             "Pohyblivost": "16/šelma", "Vytrvalost": "15/šelma", "Inteligence": "1", "Zkušenost": "60"}},
]
DOG_CHANCE = 40  # % šance na psa, hází se při každém postupu, dokud psa nemá

# Přátelé kouzelníka (PPZ, od 3. úrovně) a čaroděje (PPP, úroveň 6–10 a 11–15)
FAMILIARS = [
    {"name": "Černá kočka",
     "special": "Sedává na rameni, denně až 3 kouzla i krátce odloučená; nad 6 h a 200 sáhů magenergie usíná.",
     "base": {"Životaschopnost": "2", "Magenergie": "6", "Počet kouzel": "3",
              "Útočné číslo": "(+1 + 2) = 3, drápy", "Obranné číslo": "(+3 + 1) = 4", "Odolnost": "18",
              "Velikost": "A", "Váha": "40–70 mn", "Zranitelnost": "zvíře + M, N, P",
              "Pohyblivost": "10/šelma", "Vytrvalost": "14/šelma", "Inteligence": "10", "Charisma": "14",
              "Zkušenost": "100"},
     "caroděj": [("Životaschopnost", "3", "4"), ("Magenergie", "12", "18"), ("Počet kouzel", "6", "9"),
                 ("Útočné číslo", "(+2 + 2) = 4", "(+2 + 2) = 4"), ("Obranné číslo", "(+4 + 1) = 5", "(+4 + 1) = 5"),
                 ("Pohyblivost", "12/šelma", "12/šelma"), ("Vytrvalost", "15/šelma", "15/šelma"),
                 ("Zkušenost", "200", "300")]},
    {"name": "Havran",
     "special": "Létá; kouzlí i po několikadenním odloučení (nad 7 dní musí znovu čerpat auru).",
     "base": {"Životaschopnost": "1", "Magenergie": "5", "Počet kouzel": "2",
              "Útočné číslo": "(+1 + 2) = 3, zobák", "Obranné číslo": "(+5 + 1) = 6", "Odolnost": "14",
              "Velikost": "A", "Váha": "30–50 mn", "Zranitelnost": "zvíře + M, N, P",
              "Pohyblivost": "1 na zemi, 18 ve vzduchu/okřídlenec", "Vytrvalost": "14/okřídlenec",
              "Inteligence": "12", "Charisma": "12", "Zkušenost": "50"},
     "caroděj": [("Životaschopnost", "2", "3"), ("Magenergie", "10", "15"), ("Počet kouzel", "4", "6"),
                 ("Útočné číslo", "(+2 + 2) = 4", "(+2 + 2) = 4"), ("Obranné číslo", "(+5 + 1) = 6", "(+5 + 1) = 6"),
                 ("Pohyblivost", "1 na zemi, 19 ve vzduchu", "1 na zemi, 19 ve vzduchu"),
                 ("Vytrvalost", "15/okřídlenec", "15/okřídlenec"), ("Zkušenost", "100", "200")]},
    {"name": "Ďáblík",
     "special": "Teleportuje se do 20 sáhů (náklad do 50 mn); bojuje pařáty, nanejvýš dýkou.",
     "base": {"Životaschopnost": "3", "Magenergie": "3", "Počet kouzel": "1",
              "Útočné číslo": "(+1 + 3) = 4, pařáty", "Obranné číslo": "(+7 + 1) = 8", "Odolnost": "10",
              "Velikost": "A", "Váha": "50–80 mn", "Zranitelnost": "human. + N, P, ale O 0",
              "Pohyblivost": "13/humanoid", "Vytrvalost": "viz odolnost", "Inteligence": "14", "Charisma": "10",
              "Zkušenost": "250"},
     "caroděj": [("Životaschopnost", "4", "5"), ("Magenergie", "6", "9"), ("Počet kouzel", "2", "3"),
                 ("Útočné číslo", "(+2 + 3) = 5", "(+2 + 3) = 5"), ("Obranné číslo", "(+7 + 1) = 8", "(+7 + 1) = 8"),
                 ("Pohyblivost", "14/humanoid", "14/humanoid"), ("Zkušenost", "350", "450")]},
]
FAMILIAR_LEVEL = 3  # kouzelník si může povolat přítele od 3. úrovně (třikrát za život, každého nejvýš jednou)
FAMILIAR_NOTE = ("Kouzelník od 3. úrovně si může třikrát za život povolat přítele, každého druhu nejvýš jednou. "
                 "Přátelé kouzlí jen kouzla, která zná pán, a mají jeho přesvědčení i ZSM.")
DOG_NOTE = ("Šance na psa je 40 % (k%), hází se při každém postupu, dokud hraničář psa nemá. Pes, kterého má "
            "hraničář alespoň 5 úrovní, zesílí (PPP).")


def companion_def(kind: str, name: str) -> dict | None:
    pool = DOGS if kind == "pes" else FAMILIARS
    return next((x for x in pool if x["name"] == name), None)


def companion_stats(comp: dict, owner_cls: str, owner_level: int, owner_branch: str | None) -> dict:
    """Aktuální statistiky pomocníka podle pána (pes zesílí po 5 úrovních, čaroděj má silnější přátele)."""
    d = companion_def(comp["kind"], comp["name"])
    if d is None:
        return dict(comp.get("stats") or {})
    stats = dict(d["base"])
    if comp["kind"] == "pes":
        if int(owner_level) - int(comp.get("since", owner_level)) >= 5:
            stats = dict(d["adv"])
    elif owner_branch == "Čaroděj" and int(owner_level) >= 6:
        col = 1 if int(owner_level) <= 10 else 2
        for row in d["caroděj"]:
            stats[row[0]] = row[col]
    stats.update(comp.get("overrides") or {})
    return stats


def dog_for_roll(roll: int) -> dict | None:
    for dog in DOGS:
        lo, hi = dog["roll"]
        if lo <= roll <= hi:
            return dog
    return None
