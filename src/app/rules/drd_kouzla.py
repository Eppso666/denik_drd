"""Kouzla kouzelníka DrD 1.6 – Pravidla pro začátečníky (PPZ) a Pravidla pro pokročilé (PPP).

Číselné údaje (magenergie, past, dosah, rozsah, vyvolání, trvání, obor) jsou převzaty z pravidel,
popisy jsou jen stručná připomenutí – podrobnosti vždy v pravidlech.
Pole `min` je nejmenší magenergie, za kterou lze kouzlo seslat (None = neurčitá magenergie,
závisí např. na životaschopnosti terče).
"""
from __future__ import annotations

# (název, magenergie, min. magů, past, dosah, rozsah, vyvolání, trvání, obor, stručně)
_PPZ = [
    ("Dým", "1 mag za 2 sáhy stěny (1 mag za 3 sáhy krychlové)", 1, "", "12 sáhů",
     "stěna 3 sáhy vysoká / krychle", "1 kolo", "1–6 směn", "MA", "Kouřová clona, přes kterou není vidět."),
    ("Hyperprostor", "4 nebo 6 magů", 4, "", "0", "koule o poloměru 60 sáhů", "1 kolo", "ihned", "ČP",
     "Kouzelník se přenese na místo do 60 sáhů."),
    ("Hypnóza", "životaschopnost × 2", None, "Int+Roz – 6 – 0", "5 sáhů", "1 humanoidní postava", "1 kolo",
     "1–3 směny", "PS", "Ovládne jednoho humanoida jednoduchými příkazy."),
    ("Levitace", "3 magy první směnu, 1 mag každou další", 3, "", "dotyk", "1 tvor", "3 kola",
     "podle magenergie", "ČP", "Tvor se volně vznáší vodorovně i svisle."),
    ("Magický štít", "2 magy první kolo, 1 mag každé další", 2, "", "0", "oblast před kouzelníkem", "1 kolo",
     "podle magenergie", "EO", "Ochranná plocha – vyšší KZ a menší šance zásahu blesky."),
    ("Mágův velký mix", "(životaschopnost × 2) + 1", None, "Roz – 8 – !", "5 sáhů", "1 nestvůra", "2 kola",
     "ihned", "MA", "Promíchá tělo nestvůry v neškodný rosol."),
    ("Melenina krása", "6 magů za kolo", 6, "", "dotyk", "1 postava", "1 kolo", "podle magenergie", "VI",
     "Charisma stoupne na 21 (v 1 ze 6 případů klesne na 1)."),
    ("Metamorfóza", "11 magů za směnu", 11, "", "0", "1 tvor do 8 sáhů", "1 kolo", "podle magenergie", "MA",
     "Kouzelník se promění v bytost, na kterou se dívá."),
    ("Modré blesky", "3 magy první blesk, 2 magy každý další", 3, "", "10 sáhů", "1 nestvůra", "1 kolo",
     "ihned", "EU", "Každý blesk zraní za 1–6 životů."),
    ("Montyho čardáš", "(životaschopnost + 1) za kolo", None, "Roz – 7 – 0", "10 sáhů",
     "až 3 nestvůry v kouli 5 sáhů", "1 kolo", "podle magenergie", "PS", "Nestvůry zběsile tančí a nebojují."),
    ("Najdi neviděné", "7 magů první kolo, 6 každé další", 7, "", "8 sáhů", "koule o poloměru 2 sáhy",
     "2 kola", "podle magenergie", "PO", "Zviditelní neviděné v pravé podobě."),
    ("Nebezpečné ovoce", "3 magy za kus", 3, "", "viz pravidla", "viz pravidla", "3 kola", "ihned", "MA",
     "Výbušné hrušky, výbuch zraní za 5–10 životů."),
    ("Neviditelnost", "7 magů", 7, "", "dotyk", "1 tvor", "2 kola", "dokud neútočí", "EO",
     "Tvor i jeho výstroj jsou neviditelní."),
    ("Oheň", "2 magy za sáh vzdálenosti", 2, "", "podle magenergie", "půl sáhu", "1 kolo", "max. 1–5 směn",
     "EU", "Malý oheň jako dvě pochodně, může zapálit hořlavé věci."),
    ("Ohnivý déšť", "35 nebo 50 magů", 35, "", "20 sáhů", "kruh o poloměru 5 sáhů", "4 kola", "1 kolo", "MA",
     "Z mraku prší oheň, 1–6 životů na každý čtvereční sáh."),
    ("Protoplazma", "životaschopnost + 1", None, "Obr – 8 – 0", "10 sáhů", "1 nestvůra", "2 kola", "2–7 kol",
     "MA", "Lepkavý sliz zpomalí nestvůru na polovinu."),
    ("Rychlost", "2 magy za kolo", 2, "", "dotyk", "1 tvor", "1 kolo", "podle magenergie", "ČP",
     "Dvojnásobná rychlost – i útoky a obrany."),
    ("Sugesce", "(životaschopnost × 2) + 5", None, "Int – 6 – 0", "10 sáhů", "nejvýše 3 postavy", "2 kola",
     "1 směna", "PS", "Vsugeruje pocit (strach, únavu, vztek…)."),
    ("Světlo", "2 magy za sáh poloměru", 2, "", "0", "koule podle magenergie", "1 kolo", "1–5 směn", "EU",
     "Osvětlí okolí, světlo se pohybuje s kouzelníkem."),
    ("Ticho", "3 magy (5 magů) za sáh poloměru", 3, "", "0", "koule podle magenergie", "1 kolo", "1–5 směn",
     "EO", "Dokonalé ticho kolem kouzelníka."),
    ("Tma", "4 magy (6 magů) za sáh poloměru", 4, "", "0", "koule podle magenergie", "1 kolo", "1–5 směn",
     "EO", "Dokonalá tma, zevnitř je vidět ven."),
    ("Vodní dech", "3 magy za směnu", 3, "", "dotyk", "1 tvor", "3 kola", "podle magenergie", "MA",
     "Dýchání pod vodou."),
    ("Zaklep", "6 magů", 6, "", "20 sáhů", "1 dveře", "2 kola", "ihned", "EU",
     "Otevře zámek, závoru i kouzlo zamkni."),
    ("Zamkni", "4 magy", 4, "Sil – +8 – 0", "2 sáhy", "1 vchod", "2 kola", "2–12 směn", "EO",
     "Kouzlem zamkne dveře se zámkem nebo závorou."),
    ("Zelené blesky", "4 magy první blesk, 3 magy každý další", 4, "", "10 sáhů", "1 nestvůra", "1 kolo",
     "ihned", "EU", "Každý blesk 2–12 životů, zásah 80 %."),
    ("Zenerova karta", "7 magů za obláček", 7, "Int – 4 – 0", "10 sáhů", "tvorové o životaschopnosti 2–4",
     "2 kola", "1–3 kola", "PS", "Kdo se zadívá do obláčku, 1–3 kola nevnímá okolí."),
    ("Zlom kouzlo", "o 6 magů víc než lámané kouzlo", None, "", "dotyk", "1 tvor", "10 kol", "ihned", "EU",
     "Zruší psychické kouzlo (sugesce, hypnóza…) na postavě."),
]

_PPP = [
    ("Bábelská rybka", "5 magů", 5, "", "0", "bytosti v doslechu", "1 kolo", "3 směny", "PO",
     "Kouzelník rozumí každému mluvenému jazyku."),
    ("Beranidlo", "podle Tabulky dveří", None, "", "5 sáhů", "1 dveře", "3 kola", "ihned", "EU",
     "Dveře se rozpadnou v prach. Učí se až se 4 kouzly oboru EU."),
    ("Bílá střela", "9 magů za střelu", 9, "Roz – 7 – ⅓", "120 sáhů", "15 sáhů", "1 kolo",
     "ihned", "EU", "Výbuch bílého světla zraňuje jen magické tvory."),
    ("Bílý blesk", "5 magů", 5, "", "100 sáhů", "1 tvor", "1 kolo", "ihned", "EU",
     "Jeden blesk za kolo, zranění 1–6 životů."),
    ("Břichomluvectví", "4 magy za 10 sáhů", 4, "", "0", "koule podle magenergie", "1 kolo", "2 směny", "ČP",
     "Hlas kouzelníka vychází odkudkoli v dosahu."),
    ("Cizí jazyk", "4 magy (8 magů na jiného)", 4, "", "dotek", "1 postava", "1 kolo", "2 směny", "MA",
     "Napodobí hlas, který kouzelník slyšel."),
    ("Cizí oči", "8 magů", 8, "Int – 7 – 0", "20 sáhů", "1 živý tvor", "1 kolo", "12 směn", "PO",
     "Kouzelník vidí očima jiného tvora."),
    ("Cizí uši", "8 magů", 8, "Int – 7 – 0", "20 sáhů", "1 živý tvor", "1 kolo", "12 směn", "PO",
     "Kouzelník slyší ušima jiného tvora."),
    ("Clona myšlenek", "3 (9, 27) magy za směnu", 3, "", "dotek", "1 živý tvor", "6 kol", "podle magenergie",
     "EO", "Chrání mysl před telepatií a psychickými kouzly."),
    ("Čarodějův zámek", "7 magů", 7, "Sil – +12 – 0", "2 sáhy", "1 dveře", "1 kolo", "stále", "EO",
     "Silnější obdoba kouzla zamkni, i na dveře bez zámku."),
    ("Černý blesk", "25 magů", 25, "", "40 sáhů", "1 tvor", "1 kolo", "ihned", "EU",
     "Jeden blesk, zranění 41–56 životů."),
    ("Čtení myšlenek", "4 magy za směnu", 4, "Roz+Int – 8 – 0", "60 sáhů", "1 živý tvor", "5 nebo 10 kol",
     "podle magenergie", "PO", "Čte myšlenky tvorů s inteligencí 2 a víc."),
    ("Dubl", "3 × úroveň kouzelníka", None, "", "0", "1 dvojník", "1 kolo", "2 dny", "MA",
     "Dvojník z protoplazmy, plní jen jednoduché příkazy."),
    ("Dveřník", "15 magů", 15, "", "10 sáhů", "tunel 2 × 4 sáhy", "1 směna", "3 směny", "ČP",
     "Dočasný tunel skrz skálu nebo zeď."),
    ("Fata morgána", "4 magy za oblast 2×2×2 sáhy", 4, "Int – 8 – 0", "10 sáhů + 3 sáhy za úroveň",
     "podle magenergie", "1 kolo", "viz pravidla", "IL", "Přelud terénu (schody, dveře, jezero…)."),
    ("Fialové blesky", "6 magů první blesk, 5 magů každý další", 6, "", "koule o poloměru 10 sáhů",
     "1–3 tvorové", "1 kolo", "ihned", "EU", "Zranění 4–24 životů, zásah 68 %."),
    ("Hrom a blesky", "2 nebo 4 magy", 2, "", "doslech", "zahřmění (a blesk)", "1 kolo", "ihned", "IL",
     "Neškodné zahřmění a zablesknutí."),
    ("Hyperprostor II", "viz pravidla", None, "", "2 sáhy", "1 tvor", "1 kolo", "ihned", "ČP",
     "Silnější hyperprostor, lze seslat i na jiného. Předpokládá hyperprostor."),
    ("Kouzelná rušička", "10 magů za kolo", 10, "Roz+Int – 7 – 0", "50 sáhů", "kruh o poloměru 35 sáhů",
     "2 kola", "podle magenergie", "EO", "Hučení v hlavě – zasažení nemohou kouzlit."),
    ("Leť", "2 magy za 5 kol", 2, "", "dotek", "1 tvor", "3 kola", "podle magenergie", "ČP",
     "Volný let, nelze přitom kouzlit ani bojovat ve vzduchu."),
    ("Mrak smrti", "25 magů", 25, "Odl + Žvt – 5 – 1 život", "viz pravidla", "10 × 10 × 5 sáhů", "1 kolo",
     "6 směn", "MA", "Jedovatý mrak, který se pohybuje určeným směrem."),
    ("Najdi kouzla", "4 magy", 4, "", "20 sáhů", "koule o poloměru 5 sáhů", "1 kolo", "1 směna", "PO",
     "Odhalí kouzla a kouzelné předměty."),
    ("Najdi neviditelnost", "8 magů", 8, "", "3 sáhy za úroveň", "kruh o poloměru dosahu", "1 kolo", "6 směn",
     "PO", "Zviditelní neviditelné postavy a předměty."),
    ("Najdi předmět", "8 magů", 8, "", "0", "1 předmět do 20 sáhů + 3 sáhy za úroveň", "1 kolo", "2 směny",
     "PO", "Najde dobře známý předmět."),
    ("Najdi zlo", "5 magů", 5, "", "20 sáhů", "kruh o poloměru 20 sáhů", "1 kolo", "2 směny", "PO",
     "Zlé bytosti a předměty se rozzáří."),
    ("Neslyšitelnost", "6 magů", 6, "", "dotyk", "1 tvor", "2 kola", "viz pravidla", "EO",
     "Tvor se pohybuje naprosto neslyšně."),
    ("Neslyšitelnost do 4 sáhů", "10 magů", 10, "", "32 sáhů", "1 tvor a 4 sáhy okolí", "2 kola",
     "viz pravidla", "EO", "Neslyšitelnost pro skupinu u terče."),
    ("Neviditelnost do 4 sáhů", "11 magů", 11, "", "32 sáhů", "1 tvor a 4 sáhy okolí", "2 kola",
     "viz pravidla", "EO", "Neviditelnost pro skupinu u terče."),
    ("Nevycítitelnost", "1 mag za směnu", 1, "", "dotek", "1 tvor", "2 kola", "podle magenergie", "EO",
     "Tvora nevystopují psi ani hobití čich."),
    ("Nevycítitelnost do 4 sáhů", "3 magy za směnu", 3, "", "32 sáhů", "1 tvor a 4 sáhy okolí", "2 kola",
     "podle magenergie", "EO", "Nevycítitelnost pro skupinu u terče."),
    ("Ohnivá koule", "6 magů za kouli", 6, "Obr – 7 – 0", "90 sáhů", "koule o průměru 15 sáhů", "1 kolo",
     "ihned", "EU", "Výbuch ohně v kouli, zraňuje všechny uvnitř."),
    ("Ochrana před šípy", "9 magů", 9, "", "0", "povrch koule o poloměru 10 sáhů", "1 kolo", "10 směn", "EO",
     "Odklání šípy a malé vrhané předměty."),
    ("Ochrom bleskem", "jako příslušný blesk", None, "Int – 3–7 – 0", "12 sáhů", "1 tvor", "1 kolo", "ihned",
     "IL", "Iluzorní blesk, zranění je jen zdánlivé."),
    ("Oko", "10 magů za 6 směn", 10, "", "0", "viz pravidla", "1 kolo", "podle magenergie", "ČP+PO",
     "Neviditelné létající oko s infraviděním."),
    ("Orxanův zámek", "nejméně 15 magů", 15, "podle magenergie", "30 sáhů", "1 dveře, zámek, víko…",
     "2 kola", "stále", "EO", "Nejmocnější uzamykací kouzlo. Učí se až se 4 kouzly oboru EO."),
    ("Oživ nemrtvého", "viz pravidla", None, "", "dotek", "viz pravidla", "viz pravidla", "stále", "VI",
     "Stvoří nemrtvého služebníka. Učí se až se 2 kouzly oboru VI."),
    ("Poslání", "25 magů", 25, "Roz – 7 – 0", "10 sáhů", "1 tvor", "3 kola", "viz pravidla", "PS",
     "Přinutí tvora vykonat úkol (nebo se něčemu vyhnout)."),
    ("Přelož", "nejméně 7 magů", 7, "", "slyšitelnost nebo viditelnost", "1 text", "1 kolo", "3 směny", "PO",
     "Porozumění i psanému textu."),
    ("Přelud nebezpečí", "10 + viz pravidla", 10, "Int – 7 (0) – 0", "10 sáhů + 1 sáh za úroveň",
     "koule o poloměru dosahu", "3 kola", "20 kol", "IL",
     "Iluze tvora, kterého kouzelník viděl. Učí se až se 2 kouzly oboru IL."),
    ("Rozptyl kouzla", "nejméně 8 magů", 8, "", "32 sáhů", "krychle 8 × 8 × 8 sáhů", "1 kolo", "stále", "EU",
     "Zničí kouzelnická kouzla v oblasti."),
    ("Rudé blesky", "7 magů první blesk, 6 magů každý další", 7, "", "koule o poloměru 10 sáhů",
     "1–6 tvorů", "1 kolo", "ihned", "EU", "Zranění 5–30 životů, zásah 66 %."),
    ("Svaž postavu", "nejméně 2 × životaschopnost za postavu", None, "Roz+Sil – 5 – 0", "40 sáhů",
     "1–4 postavy", "1 kolo", "1 směna za úroveň", "PS", "Úplné ochromení humanoidů velikosti A0–C."),
    ("Zabij", "50 magů", 50, "Roz – 5 – 0", "80 sáhů", "celková životaschopnost 4–40", "1 kolo", "ihned",
     "VI", "Zabije tvory o celkové životaschopnosti 4k10."),
    ("Zašifruj", "podle uvážení", None, "viz pravidla", "1 sáh", "1 text", "5 kol", "stále", "MA",
     "Text čitelný jen po vyslovení hesla."),
    ("Zdvojení", "6 magů", 6, "", "0", "viz pravidla", "1 kolo", "6 směn", "EO+IL",
     "Vedle kouzelníka vznikne 1–5 jeho obrazů."),
    ("Zesměšni", "60 : úroveň kouzelníka", None, "Roz – 5 – 0", "5 sáhů", "1 tvor", "1 kolo", "stále", "MA",
     "Přičaruje oslí uši, dlouhý nos a podobně."),
    ("Zmatek", "12 magů", 12, "Roz – 6 – 0", "40 sáhů", "tvorové o životaschopnosti 3–18", "1 kolo",
     "12 kol", "PS", "Zmate tvory v dosahu (i přátele)."),
    ("Zmiz", "viz pravidla", None, "Roz – 10 – !", "20 sáhů", "1 tvor nebo předmět", "1 kolo", "ihned", "ČP",
     "Tvor nebo předmět zmizí. Učí se až s 5 kouzly oboru ČP."),
    ("Žluté blesky", "5 magů první blesk, 4 magy každý další", 5, "", "10 sáhů", "1 tvor", "1 kolo", "ihned",
     "EU", "Zranění 3–18 životů, zásah 72 %."),
]

FIELDS = ("name", "mana", "min", "trap", "reach", "area", "cast", "duration", "school", "desc")

SPELLS: list[dict] = (
    [dict(zip(FIELDS, s), source="PPZ") for s in _PPZ]
    + [dict(zip(FIELDS, s), source="PPP") for s in _PPP]
)
SPELL_BY_NAME = {s["name"]: s for s in SPELLS}

SCHOOLS = {"ČP": "časoprostorová", "EU": "energetická útočná", "EO": "energetická ochranná",
           "IL": "iluzionistická", "MA": "materiální", "VI": "vitální", "PS": "psychická", "PO": "poznávání"}

# Kouzla, která mág od 6. úrovně sesílá přímo; ostatní nová kouzla jen přes dvířka/dveře/bránu.
MAG_DIRECT = ["Cizí jazyk", "Clona myšlenek", "Čtení myšlenek", "Fata morgána", "Hypnóza", "Montyho čardáš",
              "Poslání", "Sugesce", "Zenerova karta"]
MAG_HELPERS = [
    ("Dvířka", "1 mag", "Sešle libovolné kouzlo, šance na úspěch −50 %."),
    ("Dveře", "0,5 × magenergie kouzla", "Sešle libovolné kouzlo za 1,5× magenergii."),
    ("Brána", "stejná jako u kouzla", "Viz PPP – nejdražší, ale nejspolehlivější pomocné kouzlo."),
]

# Tabulka magenergie (po zaostření vůle) podle úrovně a inteligence; sloupce INT 8–9, 10–11, … 20–21
MANA_COLS = [(8, 9), (10, 11), (12, 13), (14, 15), (16, 17), (18, 19), (20, 21)]
WIZARD_MANA = {
    1: [7, 7, 8, 8, 8, 9, 9],
    2: [10, 11, 12, 12, 12, 13, 14],
    3: [12, 14, 15, 16, 17, 18, 20],
    4: [14, 17, 19, 20, 21, 23, 26],
    5: [17, 20, 22, 24, 26, 28, 31],
    6: [19, 23, 26, 28, 30, 33, 37],
    7: [21, 26, 29, 32, 35, 38, 43],
    8: [24, 29, 33, 36, 39, 43, 48],
    9: [26, 32, 36, 40, 44, 48, 54],
    10: [27, 35, 39, 44, 48, 53, 60],
    11: [29, 37, 42, 47, 52, 57, 65],
    12: [30, 38, 44, 50, 56, 62, 70],
    13: [33, 42, 49, 55, 61, 68, 77],
    14: [36, 45, 53, 60, 67, 75, 84],
    15: [39, 49, 57, 65, 73, 81, 91],
}
SPELL_COUNT = {1: 3, 2: 5, 3: 7, 4: 9, 5: 11, 6: 14, 7: 17, 8: 20, 9: 23, 10: 26, 11: 30, 12: 34, 13: 38,
               14: 42, 15: 46}
# Pravděpodobnost úspěchu kouzelníka podle inteligence
SUCCESS = [(9, 32), (12, 47), (14, 61), (16, 74), (18, 85), (20, 95), (99, 99)]


def wizard_mana(level: int, intel: int) -> int:
    lvl = max(1, min(15, int(level)))
    col = 0
    for i, (lo, hi) in enumerate(MANA_COLS):
        if intel >= lo:
            col = i
    return WIZARD_MANA[lvl][col]


def spell_count(level: int) -> int:
    return SPELL_COUNT[max(1, min(15, int(level)))]


def success_chance(intel: int) -> int:
    for top, pct in SUCCESS:
        if intel <= top:
            return pct
    return 99


def available_spells(branch: str | None, level: int) -> list[dict]:
    """Kouzla, ze kterých si postava může vybírat. PPP kouzla až od 6. úrovně."""
    out = [s for s in SPELLS if s["source"] == "PPZ" or int(level) >= 6]
    return out
