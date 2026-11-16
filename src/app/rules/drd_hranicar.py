"""Hraničář DrD 1.6: kouzla (PPZ str. 41–42), kouzla druida a chodce (PPP str. 11–23)
a mimosmyslové schopnosti (PPZ str. 38–40, PPP str. 12–13).

Hraničář kouzla nevybírá – zná všechna kouzla svého povolání a oboru, jakmile dosáhne potřebné úrovně.
Číselné údaje jsou z pravidel, popisy jsou jen stručné připomenutí.
"""
from __future__ import annotations

# (název, magenergie, min. magů, dosah, rozsah, vyvolání, trvání, stručně)
_RANGER = [
    ("Mluv se zvířaty", "3 magy první kolo, 2 magy každé další", 3, "20 sáhů", "1 zvíře", "2 kola",
     "podle magenergie", "Rozhovor s jedním zvířetem."),
    ("Najdi stopy", "3 magy", 3, "0", "jen hraničář", "2 kola", "6 směn", "+25 % ke stopování."),
    ("Najdi zvíře", "3 magy", 3, "5 mil", "nejbližší zvíře daného druhu", "2 kola", "ihned",
     "Hraničář ví, kde je nejbližší zvíře zvoleného druhu."),
    ("Neutralizuj jed", "6 magů", 6, "dotyk", "1 postava", "1 kolo", "stále", "Sníží nebezpečnost jedu o 6."),
    ("Odstraň ochromení", "4 magy", 4, "dotyk", "1 postava", "2 kola", "ihned", "Zruší ochromení."),
    ("Uzdrav lehká zranění", "3 magy", 3, "dotyk", "1 postava", "3 kola", "stále", "Vyléčí 2–7 životů (1k6+1)."),
    ("Uzdrav nemocného", "12 magů", 12, "dotyk", "1 postava", "2 směny", "stále", "Vyléčí nemoc."),
    ("Uzdrav těžká zranění", "5 magů", 5, "dotyk", "1 postava", "3 kola", "stále",
     "Vyléčí 4–14 životů (2k6+2)."),
    ("Zmam osobu", "podle inteligence terče × úroveň", None, "7 sáhů", "1 tvor", "3 kola", "viz pravidla",
     "Terč považuje hraničáře za přítele. Šance a magenergie podle tabulky inteligence a zmámení."),
]

# Tabulka inteligence a zmámení: (nejvyšší INT, úspěch %, kontrola jednou za, magů na úroveň terče)
CHARM = [(0, 0, "–", None), (1, 15, "4 hodiny", 6), (5, 80, "1 den", 5), (10, 60, "12 hodin", 5),
         (14, 40, "5 hodin", 6), (17, 20, "4 hodiny", 6), (19, 10, "2 hodiny", 6), (20, 8, "1 hodinu", 7),
         (99, 5, "3 směny", 7)]

# Kouzla společná druidovi i chodci od 6. úrovně (PPP str. 11–12)
_SHARED = [
    ("Chraň před dračím dechem", "10 magů", 10, "dotyk", "1 tvor", "1 kolo", "3 směny",
     "Proti dračímu dechu dvojnásobné OČ, zranění poloviční."),
    ("Magické zrcadlo", "nejméně 8 magů", 8, "0", "kruh o poloměru 2 sáhy", "1 kolo", "podle magenergie",
     "Pole pohlcuje nebo odráží útočná kouzla mířená na hraničáře."),
    ("Odčaruj zkamenění", "30 magů", 30, "dotyk", "1 tvor", "1 směna", "stále",
     "Oživí zkamenělou postavu (ne kouzelnické zkamenění)."),
    ("Ošetři zranění chladem", "8 magů", 8, "dotyk", "1 tvor", "1 směna", "stále",
     "Vrátí 15–20 životů ztracených mrazem (zranění do 3 směn)."),
    ("Ošetři zranění kyselinou", "6 magů", 6, "dotyk", "1 tvor", "1 směna", "stále",
     "Vrátí 11–16 životů ztracených kyselinou (zranění do 3 směn)."),
    ("Ošetři zranění ohněm", "9 magů", 9, "dotyk", "1 tvor", "1 směna", "stále",
     "Vrátí 17–22 životů ztracených ohněm (zranění do 3 směn)."),
    ("Telepatická ochrana", "10 magů", 10, "dotyk", "1 tvor", "1 směna", "1 den",
     "Ochrana před nepovolenou telepatií a psychickými kouzly hraničáře."),
    ("Úder varování", "7 magů", 7, "9 sáhů", "1 tvor", "2 kola", "stále", "Zranění 2–7 životů."),
    ("Úder zloby", "7 magů", 7, "9 sáhů", "1 tvor", "2 kola", "stále", "Zranění 4–14 životů."),
    ("Úder nenávisti", "12 magů", 12, "12 sáhů", "1–3 tvorové", "1 kolo", "stále",
     "Celkem 3–30 životů rozdělených rovnoměrně mezi terče."),
    ("Úkryt", "3 × životaschopnost", None, "dotyk", "1 živý tvor", "2 kola", "viz pravidla",
     "Přenese duši souhlasícího tvora do neživého předmětu."),
    ("Vládni přirozeným věcem", "6 magů", 6, "dotyk", "1 věc (do 2×2×2 sáhů)", "4 kola", "stále",
     "Uprosí věc z přírodního materiálu, aby splnila přání."),
]

# Druidova lesní kouzla (PPP str. 16–18): + četnost a nejnižší úroveň
_DRUID = [
    ("Cit dřeva", "2 magy", 2, "–", "–", "1 kolo", "ihned", "kdykoliv", 6,
     "Dlaň na kmeni: nejbližší čistý vodní zdroj."),
    ("Cit kamene", "2 magy", 2, "–", "koule o poloměru 50 sáhů", "1 kolo", "ihned", "kdykoliv", 6,
     "Dlaň na skále: blízké jeskyně a prameny."),
    ("Cit vody", "2 magy", 2, "–", "–", "1 kolo", "ihned", "kdykoliv", 6, "Pozná, zda pramen není škodlivý."),
    ("Cit země", "2 magy", 2, "–", "–", "1 kolo", "ihned", "kdykoliv", 6, "Pozná jedovaté lesní plodiny."),
    ("Hněv lesa", "veškerá současná", 1, "–", "okruh o poloměru 50 sáhů", "1 kolo", "1 směna",
     "1× mezi dvěma úplňky", 6, "Les se obrátí proti vetřelcům, padá na ně hrůza."),
    ("Láska lesa", "veškerá současná", 1, "–", "1 osoba", "1 kolo", "viz pravidla", "1× ročně", 6,
     "Odmění osobu, která se zasloužila o les."),
    ("Najdi bytost", "10 magů", 10, "–", "okruh o poloměru 10 mil", "1 směna", "ihned",
     "úspěšně 1× denně", 6, "Najde bytost či skupinu bytostí v okruhu 10 mil."),
    ("Orientace", "1 mag", 1, "–", "družina", "1 kolo", "viz pravidla", "kdykoliv", 6,
     "Družina projde hustým lesem skoro jako po cestě."),
    ("Pouto krve", "veškerá současná", 1, "–", "1 zvíře / smečka", "1 kolo", "1 den",
     "1× mezi dvěma úplňky", 9, "Zraněný druid uprosí lesní zvíře, aby neútočilo."),
    ("Pouto lásky", "veškerá současná", 1, "–", "1 osoba", "1 směna", "stále", "1× mezi dvěma úplňky", 12,
     "Vrátí život mrtvé postavě, která byla druidovi drahá."),
    ("Pouto života", "veškerá současná", 0, "–", "druid", "1 kolo", "viz pravidla", "3× za život", 15,
     "Druid se vydá do ochrany lesní moci."),
    ("Temnota", "10 magů", 10, "–", "okruh o poloměru 300 sáhů", "1 kolo", "viz pravidla",
     "4× mezi dvěma úplňky", 6, "Neproniknutelná tma kolem druida."),
]
# Pomocná lesní kouzla – obnoví schopnost sesílat lesní kouzla; vyvolání 2 směny, 1× denně na osobu
DRUID_HELPERS = [("Přání", 15, 6), ("Prosba", 30, 9), ("Stesk", 45, 12), ("Nářek", 60, 15)]

# Chodcova kouzla pocestných (PPP str. 18–20)
_TRAVEL = [
    ("Ochrana před bouří", "10 magů", 10, "0", "kopule 2 sáhy", "1 kolo", "dokud chodec sedí",
     "Kopule ztuhlého vzduchu chrání před bouří (svíce a pouštní písek)."),
    ("Ochrana před deštěm", "2 magy za 1×1 sáh", 2, "0", "podle magenergie", "1 kolo", "viz pravidla",
     "Stříška, pod kterou neprší (pouštní písek)."),
    ("Ochrana před vlky", "1 mag za osobu", 1, "dotyk", "osoby", "1 kolo", "1 den",
     "Stopa páchne rozzuřenou medvědicí, vlci ji nesledují."),
    ("Ochrana před zimou", "5 magů", 5, "dotyk", "1 osoba", "1 kolo", "1 den",
     "Postava nevnímá mráz; potom past Odl – 5."),
    ("Přivolej druida", "4 magy", 4, "hvozd", "hvozd", "1 směna", "ihned",
     "Všichni druidové v hvozdu uslyší „jsem zde“."),
    ("Rozdělej oheň", "4 magy", 4, "0", "hromada klestí", "1 směna", "viz pravidla",
     "Rozdělá oheň i z mokrého dřeva."),
]
# Kouzla chodcova meče (PPP str. 20–22)
_SWORD = [
    ("Dvojitý sek", "8 magů", 8, "0", "chodec", "–", "1 kolo", "Dva útoky v kole (iniciativa +6)."),
    ("Odraz projektily", "2, 4, 6, 8 magů", 2, "0", "chodec", "–", "1 kolo",
     "Odrazí vržený předmět, hvězdici i na jiný terč."),
    ("Odraz šípy", "3, 6 magů", 3, "0", "chodec", "–", "1 kolo", "Odrazí šíp nebo šipku z kuše."),
    ("Poškození zbraně", "5 magů", 5, "0", "zbraň soupeře", "–", "1 kolo", "Výpad, který poškodí zbraň soupeře."),
    ("Prasátko", "2 magy", 2, "0", "1 soupeř", "–", "viz pravidla", "Za slunce oslní soupeře čepelí."),
    ("Svítící čepel", "1 mag", 1, "0", "meč", "–", "3 směny", "Čepel matně svítí."),
    ("Transmutace kovu", "4 magy", 4, "0", "meč", "–", "stále", "Změní kov meče (ocel ↔ stříbro…)."),
    ("Uspání démona", "viz pravidla", None, "dotyk", "zbraň / předmět", "–", "podle magenergie",
     "Uspí démona v kouzelné zbrani."),
]
# Psychická kouzla chodce (PPP str. 22–23)
_PSYCH = [
    ("Odhal vinu", "3 magy", 3, "10 sáhů", "1 osoba", "1 kolo", "ihned",
     "Vina či nevina osoby pod uhrančivým pohledem."),
    ("Odveď pozornost", "5 magů", 5, "20 sáhů", "skupina osob", "1 kolo", "viz pravidla",
     "Odvede pozornost od tématu, předmětu nebo osoby."),
    ("Uhrančivý pohled", "2 magy", 2, "do očí", "viz pravidla", "1 kolo", "3 směny",
     "Kdo neodolá pasti, chová se k chodci s bázní."),
    ("Uspi okolí", "7 magů", 7, "25 sáhů", "skupina osob", "1 směna", "viz pravidla",
     "Okolí do 2 směn usne."),
    ("Zrcadlo vzpomínek a melancholie", "9 magů", 9, "40 sáhů", "1 osoba", "1 kolo", "6 směn",
     "Na hodinu zlepší přesvědčení uhranuté osoby."),
]


def _mk(rows, group: str, frm: int, src: str) -> list[dict]:
    out = []
    for r in rows:
        name, mana, mn, reach, area, cast, dur, desc = r
        out.append({"name": name, "mana": mana, "min": mn, "trap": "", "reach": reach, "area": area, "cast": cast,
                    "duration": dur, "school": group, "desc": desc, "source": src, "from_level": frm,
                    "freq": ""})
    return out


SPELLS: list[dict] = (
    _mk(_RANGER, "hraničář", 2, "PPZ")
    + _mk(_SHARED, "druid i chodec", 6, "PPP")
    + [{"name": n, "mana": m, "min": mn, "trap": "", "reach": r, "area": a, "cast": c, "duration": du,
        "school": "lesní", "desc": ds, "source": "PPP", "from_level": lv, "freq": f}
       for n, m, mn, r, a, c, du, f, lv, ds in _DRUID]
    + _mk(_TRAVEL, "pocestných", 6, "PPP")
    + _mk(_SWORD, "chodcův meč", 6, "PPP")
    + _mk(_PSYCH, "psychické", 6, "PPP")
)
SPELL_BY_NAME = {s["name"]: s for s in SPELLS}
GROUPS = {"druid": ["druid i chodec", "lesní"],
          "chodec": ["druid i chodec", "pocestných", "chodcův meč", "psychické"]}


def ranger_spells(level: int, branch: str | None) -> list[dict]:
    """Kouzla, která hraničář na dané úrovni a v daném oboru zná (bez ohledu na úroveň u lesních kouzel)."""
    level = int(level)
    if level < 2:
        return []
    out = [s for s in SPELLS if s["school"] == "hraničář"]
    if level >= 6 and branch in ("Druid", "Chodec"):
        groups = GROUPS[branch.lower()]
        out += [s for s in SPELLS if s["school"] in groups]
    return out


def charm_row(intel: int) -> tuple[int, str, int | None]:
    for top, pct, check, per in CHARM:
        if intel <= top:
            return pct, check, per
    return CHARM[-1][1:]


# --- mimosmyslové schopnosti ------------------------------------------------------------------

ABILITIES = ["Telekineze", "Pyrokineze", "Telepatie"]
ABILITY_ROLL = [(40, "Telekineze"), (75, "Pyrokineze"), (100, "Telepatie")]
ABILITY_DESC = {
    "Telekineze": "Pohyb volně položených předmětů silou vůle, 1 sáh za kolo. "
                  "Největší vzdálenost (sáhy) = hodnota z tabulky / váha v mincích.",
    "Pyrokineze": "Zapálení nejvýš 10 mincí hořlavé látky. Počet kol na pokus = hodnota z tabulky / vzdálenost "
                  "v sázích. Hraničář se nesmí bránit ani bojovat.",
    "Telepatie": "Přenos a čtení myšlenek. Hody proti pasti podle Tabulky čtení mysli "
                 "(povolené vnuknutí 1, čtení 2, nepovolené vnuknutí 6, čtení 7 – opraveno o Int terče).",
}
# stupeň znalosti 1–12
TELEKINESIS = [150, 300, 450, 600, 750, 900, 1000, 1100, 1200, 1300, 1400, 1500]
PYROKINESIS = [75, 150, 225, 300, 375, 450, 500, 550, 600, 650, 700, 750]
# základní vzdálenost (sáhy) a tloušťky dřeva, kamene, kovu (coulů), které ji zkrátí o 2 sáhy
TELEPATHY = [(100, 50, 10, 1), (150, 60, 12, 2), (200, 70, 14, 3), (250, 80, 16, 4), (300, 90, 18, 5),
             (350, 100, 20, 6), (375, 105, 21, 6), (400, 110, 22, 7), (425, 115, 23, 7), (450, 120, 24, 8),
             (475, 125, 25, 8), (500, 130, 26, 9)]
MIND_READING = [("povolené vnuknutí", 1, "−Int terče", "hraničář", "Int"),
                ("povolené čtení", 2, "−Int terče", "hraničář", "Int"),
                ("nepovolené vnuknutí", 6, "+Int terče", "hraničář", "Int+Roz"),
                ("nepovolené čtení", 7, "+Int terče", "hraničář", "Int+Roz"),
                ("odhalení", 4, "+Int hraničáře", "terč", "Int+Roz"),
                ("uzavření", 6, "+Int hraničáře", "terč", "Int+Roz")]
FIRST_ABILITY_LEVEL = 4
EXTRA_ABILITY = {"Druid": (8, 12), "Chodec": (12,)}


def ability_roll(r: int) -> str:
    for top, name in ABILITY_ROLL:
        if r <= top:
            return name
    return ABILITY_ROLL[-1][1]


def ability_grade(level: int, since: int) -> int:
    """Stupeň znalosti: kolikátou úroveň se jí hraničář věnuje (1–12)."""
    return max(1, min(12, int(level) - int(since) + 1))


def ability_value(name: str, grade: int) -> str:
    g = max(1, min(12, grade)) - 1
    if name == "Telekineze":
        return f"součin váhy a vzdálenosti {TELEKINESIS[g]}"
    if name == "Pyrokineze":
        return f"součin času a vzdálenosti {PYROKINESIS[g]}"
    base, wood, stone, metal = TELEPATHY[g]
    return (f"dosah {base} sáhů; −2 sáhy za každých {wood} coulů dřeva, {stone} coulů kamene, "
            f"{metal} {'coul' if metal == 1 else 'coulů'} kovu")


def ability_slots(level: int, branch: str | None) -> int:
    level = int(level)
    if level < FIRST_ABILITY_LEVEL:
        return 0
    n = 1
    if level >= 6 and branch in EXTRA_ABILITY:
        n += sum(1 for lv in EXTRA_ABILITY[branch] if level >= lv)
    return n
