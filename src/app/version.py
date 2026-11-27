"""Číslo verze a novinky, které se po aktualizaci ukážou na úvodní obrazovce."""
from __future__ import annotations

VERSION = "0.16.2"

CHANGES: dict[str, list[str]] = {
    "0.16.2": [
        "Smazání kampaně v Doupěti pána jeskyně (podržením karty i ze Stolu PJ) ji ukončí i hráčům – "
        "při další synchronizaci se jim odpojí a postavy jim zůstanou.",
        "Bez spojení se serverem se kampaň nesmaže, aby hráčům nezůstala přístupná.",
    ],
    "0.16.1": [
        "Úpravy od PJ (životy, zkušenosti, předměty, zásah v souboji, zkušenosti za boj) a tajné zprávy "
        "se opravdu dostanou k hráči: zapíší se do jeho deníku při další synchronizaci a hráč uvidí upozornění.",
        "PJ vidí upravené životy hned; dokud úpravu hráč nepřevezme, je u něj „úprava čeká na hráče“.",
        "Na serveru je potřeba jednou spustit skript supabase/upravy_pj.sql.",
    ],
    "0.16.0": [
        "Kampaň z Doupěte pána jeskyně se zakládá na serveru družiny: PJ dostane kód a pošle ho hráčům.",
        "Hráči se připojí kódem u své postavy v Družině → Připojit se; PJ na Stole PJ vidí hráče, jejich "
        "životy, deníky a hody, sdílí mapy a mění sezení.",
        "V Družině u postavy už nejde zakládat kampaň – zakládá ji jen Pán jeskyně v Doupěti.",
    ],
    "0.15.0": [
        "Úvod: Hráč (moje postavy) nebo Pán jeskyně (Doupě pána jeskyně – moje příběhy).",
        "Pán jeskyně zakládá kampaň s názvem a heslem; Stůl PJ se bez hesla neotevře. Hráči se připojí jen kódem "
        "kampaně (propojení s hráči připravujeme).",
        "Postava: úroveň v kroužku u portrétu, schopnosti jen do aktuální úrovně, „+“ pro vlastní dovednost, "
        "Společník u hraničáře a kouzelníka; klepnutí na zbraň otevře Kostky → Souboj.",
        "Kostky → Souboj: útok vybranou zbraní a obrana složená z vybavených předmětů.",
        "Postup na úroveň: Hod na životy a magenergii s dotazem na zálohu a tlačítkem Zpět.",
        "Deník → Postava: přesvědčení a příběh postavy.",
        "Seslání kouzla: okno výsledku (padlo vs. potřeba), hod na zranění, zásah nebo léčení podle pravidel, "
        "past pro terč; při zadávání magenergie přepočet (např. 7 magů = 3 blesky). Stejné okno u výroby alchymisty.",
        "Bestiář je jen u Pána jeskyně – hráč ho ve spodní liště nemá.",
    ],
    "0.14.0": [
        "Nová úvodní obrazovka a obrazovka Nová postava podle grafického návrhu.",
        "Stůl PJ a propojení u stolu jsou zatím odložené (vrátí se před zveřejněním aplikace); "
        "Družina funguje jako ve verzi 0.12 – připojení kódem kampaně.",
    ],
    "0.13.1": [
        "Dračí doupě: přesvědčení pod jménem postavy – výběr z pěti, nebo hod k10 podle rasy.",
        "Předměty mají vlastní popis; ukáže se v batohu i v detailu předmětu (klepnutím).",
        "Kostky ve tvaru skutečných kostek (k4 až k20, k6+, k%), hozené číslo uvnitř kostky.",
        "Vybraná schopnost výrazně svítí a úpravu od PJ jde napsat ručně (−100 až +100 %).",
    ],
    "0.13.0": [
        "Oddělený Stůl PJ: Pán jeskyně vede kampaň bez postavy – Kampaň, Souboj, Bestiář PJ, Nástroje a Poznámky.",
        "PJ přijímá hráče, zamyká kampaň a smí hráčům měnit životy a zkušenosti, poslat předmět nebo tajnou zprávu; "
        "hráč to uvidí v Družině a změna se propíše do jeho deníku.",
        "Propojení: U stolu (telefon PJ je stůl, stejná Wi-Fi, bez internetu – jen v aplikaci) nebo Vlastní server "
        "PJ s průvodcem ve 4 krocích a pozvánkou přes QR nebo odkaz.",
        "Souboj PJ s jednou iniciativou pro hráče i nestvůry, zkušenosti za boj k rozdělení družině.",
    ],
    "0.12.0": [
        "Družina je propojená přes internet: PJ založí kampaň a pošle kód, hráči se připojí svou postavou.",
        "Členové s životy a stavem online, živé hody družiny (skryté hody PJ), mapy od PJ se uloží do Deníku, "
        "PJ vidí deníky hráčů. Bez internetu se hraje dál a vše se odešle po připojení.",
    ],
    "0.11.0": [
        "Družina: na kartě postavy se připojíš ke kampani kódem od PJ, nebo ji jako PJ založíš. "
        "Propojení s ostatními hráči se zapne, až bude nastavený server.",
    ],
    "0.10.0": [
        "Nový vzhled podle grafického návrhu: Dračí doupě ve stylu Fire Fantasy (tmavý kámen, bronz, zlato, "
        "rudá záře, pergamen), Dračí Hlídka ve stylu Ice Fantasy (temně modrá, stříbro, ledová záře).",
        "Kovové rámečky, ilustrace v záhlaví postavy, nová horní lišta a spodní navigace, písmo Cinzel.",
    ],
    "0.9.0": [
        "Záloha a obnova všech postav do souboru (úvodní obrazovka) a zmenšování obrázků.",
        "Souboj podle pravidel: rasová zbraň +1, beze zbraně OZ −3, velikost, mez vyřazení, postihy za zranění, "
        "naložení a únavu (DH), dostřely střelných zbraní.",
        "Postup na úroveň podle tabulek zkušeností a životů, DH dovednostní a charakterové body, tabulky many.",
        "Hraničář: kouzla, kouzla druida a chodce a mimosmyslové schopnosti. Alchymista: výroba předmětů.",
        "Aktivní kouzla s odpočtem trvání, hledání v katalogu a kouzlech, omezení zbraní a zbrojí povolání.",
        "Pohyb a pozornost na kartě, tabulka zkušeností (klepni na Zkušenosti) a tisk listu postavy.",
    ],
}


def news_since(seen: str | None) -> list[tuple[str, list[str]]]:
    """Novinky verzí novějších než naposledy viděná (None = nový uživatel → nic)."""
    if not seen:
        return []

    def key(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split(".") if x.isdigit())
    return [(v, CHANGES[v]) for v in sorted(CHANGES, key=key, reverse=True) if key(v) > key(seen)]
