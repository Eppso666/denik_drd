# Deník dobrodruha

Mobilní deník postavy pro **Dračí Hlídku** a **Dračí doupě 1.6**. Napsáno v Pythonu (Flet 1.1).
Android dostane instalační soubor `.apk`, iPhone webovou verzi, kterou si přidá na plochu jako aplikaci.

## Co aplikace umí (verze 0.10)

- **Výběr postavy** a **generátor postavy** (automaticky podle pravidel, nebo ručně).
- Po výběru postavy se otevře **samostatná větev její hry**: jiný vzhled, jiné kostky, jiná pravidla, vlastní bestiář.

| | Dračí Hlídka | Dračí doupě 1.6 |
|---|---|---|
| Vzhled | tmavý, oranžový | pergamen, vínová |
| Kostky | k6, k6+, k10 | k4, k6, k8, k10, k12, k20 (i víc kostek naráz), k6+, k%|
| Generátor | 6× k6, nejnižší se škrtá; nebo 20 bodů (1–6 na vlastnost); + rodový základ, +3 ke 2 dominantním | rozsahy podle rasy, základní vlastnosti povolání podle tabulky povolání + opravy rasy |
| Ověřovací hod | 1k10 + oprava + stupeň dovednosti, musí **překonat** obtížnost; výhoda/nevýhoda ±5 | schopnosti v %: k% ≤ šance; past: 1k10 + oprava ≥ nebezpečnost |
| Boj | ÚČ = útočnost + SIL (střelba + OBR), OČ = ZO + obrana zbraně + štít, ZO = OBR + kvalita zbroje | ÚČ = oprava SIL (střelba OBR) + síla zbraně, OČ = oprava OBR + kvalita zbroje + obrana zbraně; útok i obrana k6+ |
| Životy | 10 + ODO, hranice smrti −(10 + ODO) | základ povolání + ODL, při postupu kostka povolání + ODL (min. 1) |

- **Postava**: životy, mana, vlastnosti s opravami, zbraně s ÚČ/OČ, dovednosti; úprava všech údajů.
- **Postup na úroveň**: ruční úprava úrovně, životů, many, vlastností (a v DrD hod na přírůstek životů).
- **Schopnosti povolání DrD** se doplňují samy podle povolání a úrovně (zloděj: tabulka Pravděpodobnost úspěchu
  zloděje + násobek opravy; hraničář: stopování a pes). Generátor je ukazuje pro úroveň 1–5 i se základními
  vlastnostmi povolání.
- **Obory DrD od 6. úrovně** (Pravidla pro pokročilé): při postupu z 5. na 6. úroveň si postava vybere jeden ze
  dvou oborů (bojovník/šermíř, druid/chodec, theurg/pyrofor, mág/čaroděj, lupič/sicco) a na kartě se jí ukážou
  jeho schopnosti podle úrovně; lupič a sicco mají procenta z tabulek pro úrovně 6–15.
- **Kouzla DrD**: kouzelník (a od 6. úrovně čaroděj či mág) si vybírá kouzla z PPZ (27) a od 6. úrovně i z PPP
  (49) – s limitem počtu kouzel podle úrovně, jen ta, na která má magenergii, mág s omezením přímého sesílání.
  Kouzlo jde seslat: odečte magenergii a hodí k% na úspěch podle inteligence. Magenergie podle tabulky.
- **Pomocníci DrD**: tlačítko ⊕ u Vlastností – kouzelník si povolá černou kočku, havrana nebo ďáblíka, hraničář
  psa (výběr nebo hod k%). Pod vlastnostmi se ukáže karta pomocníka s jeho vlastnostmi; pes po 5 úrovních
  a přátelé čaroděje zesílí podle PPP.
- **Portrét** postavy v kroužku (obrázek z galerie či disku).
- **Vlastní dovednosti** (DH: vlastnost + stupeň; DrD: šance v %).
- **Batoh**: předměty, výbava na těle, peníze, **naložení automaticky z vah nebo ručně**, nosnost podle pravidel.
  **Katalog z pravidel** (DrD: PPZ, DH: Příručka pro hráče): zbraně, střelné a vrhací zbraně, zbroje podle
  velikosti rasy, štíty, výstroj – přidat nebo rovnou koupit (odečte cenu). Vlastní předměty lze uložit jako
  šablony do „Moje předměty“.
- **Kostky**: výběr dovednosti / zbraně / schopnosti / pasti, na kterou házíš, a volné hody.
- **Souboj**: soupeř z bestiáře nebo vlastní, útok, obrana, zranění, iniciativa, průběh kol.
- **Bestiář** zvlášť pro každou hru (DrD v klasickém zápisu: životaschopnost, útok, obrana, …), s obrázkem.
- **Deník**: poznámky se štítky a připnutím, **obrázky** (mapy, portréty) z fotoaparátu nebo galerie.
- **Hraničář DrD**: kouzla od 2. úrovně, kouzla druida a chodce (PPP) od 6. úrovně, mimosmyslové schopnosti
  (telekineze, pyrokineze, telepatie) se stupněm znalosti a tabulkami.
- **Alchymista DrD**: výroba předmětů z PPZ (lektvary, svitky, trvalé předměty, jedy, nemagické) – odečte
  magenergii a suroviny z truhly, hodí k% podle obratnosti a hotový předmět vloží do batohu.
- **Aktivní účinky** s odpočtem trvání (kola, směny, hodiny, dny), **hledání** v katalogu a kouzlech.
- **Souboj podle pravidel**: rodová zbraň +1 ÚČ, beze zbraně OZ −3, obojruční zbraně bez štítu, velikost,
  mez vyřazení a postih za zranění, naložení, únava (DH), ÚČ střelných zbraní podle dostřelu, omezení výzbroje povolání.
- **Postup** podle tabulek zkušeností (klepnutím na Zkušenosti se ukáže celá tabulka), přírůstek životů,
  DH dovednostní a charakterové body, tabulky many a magenergie.
- **Tisk listu postavy** (ikona tiskárny) – uloží HTML, které se v prohlížeči vytiskne nebo uloží jako PDF.
- **Záloha a obnova** všech postav do souboru (úvodní obrazovka) a připomínka zálohy po 14 dnech.
- Vše se ukládá **jen v zařízení** (proto zálohuj).
- **Stůl PJ** (úvod → Vedu hru): Pán jeskyně vede kampaň bez postavy – Kampaň (přijímání hráčů, zámek, úprava
  životů, zkušeností a předmětů hráčů), Souboj (jedna iniciativa pro hráče i nestvůry), Bestiář PJ, Nástroje
  (zkušenosti za boj) a Poznámky (tajné poznámky, připravené mapy, tajná zpráva hráči). Hráč nic z toho nevidí.
- **Družina** (karta na postavě): připojení ke stolu PJ nebo pozvánkou na server PJ, čekání na schválení,
  úpravy a zprávy od PJ, hody družiny, mapy od PJ do Deníku.

## Jak dostat aplikaci do telefonu

### 1. Nahraj projekt na GitHub (jednou)

1. Na github.com vytvoř nový repozitář, např. `denik-dobrodruha`. Aby šla zdarma zveřejnit webová verze
   (GitHub Pages), musí být **veřejný** (Public).
2. Nahraj do něj obsah této složky. Bez instalace gitu: v repozitáři **Add file → Upload files**, přetáhni
   všechny soubory a složky (včetně skryté složky `.github`) a potvrď **Commit changes**.
   Pokud prohlížeč složku `.github` nepřetáhne, vytvoř soubor ručně přes **Add file → Create new file**,
   název `.github/workflows/build.yml`, a vlož do něj obsah stejnojmenného souboru.
3. **Settings → Pages → Build and deployment → Source: GitHub Actions.**

### 2. (Doporučeno) Podpisový klíč pro Android

Bez něj se každá nová verze podepíše jiným klíčem a telefon ji nenainstaluje přes starou. Musel bys
starou odinstalovat, a tím smazat postavy.

```bash
pip install cryptography
python scripts/create_signing_key.py
```

Na GitHubu v **Settings → Secrets and variables → Actions → New repository secret** přidej:

- `ANDROID_KEYSTORE_BASE64` = obsah souboru `upload-keystore.base64.txt`
- `ANDROID_KEYSTORE_PASSWORD` = heslo, které jsi zvolil

Soubory klíče ulož bezpečně mimo repozitář a nikomu je neposílej.

### 3. Sestavení

Každé nahrání změn spustí sestavení (záložka **Actions**, trvá zhruba 15–25 minut). Ručně: **Actions →
Sestavení aplikace → Run workflow**.

- **Android:** v dokončeném běhu dole v sekci **Artifacts** stáhni `denik-dobrodruha-android` (zip),
  rozbal ho a soubor `.apk` pošli hráčům. Při instalaci je potřeba povolit „instalaci z neznámých zdrojů“.
- **iPhone:** webová verze je na adrese `https://<tvé-jméno>.github.io/denik-dobrodruha/`.
  V Safari otevři adresu, klepni na **Sdílet → Přidat na plochu**. Data se ukládají v prohlížeči
  (pozor: smazáním dat Safari se smažou i postavy; místo na obrázky je omezené zhruba na 5 MB).

## Vývoj na počítači

```bash
pip install flet==1.1.2 flet-cli==1.1.2 flet-desktop==1.1.2 pytest
bash scripts/fetch_fonts.sh      # volitelně: písma Cinzel, IM Fell, Alegreya Sans
flet run src/main.py             # okno aplikace
flet run --web src/main.py       # v prohlížeči
pytest -q                        # testy pravidel a všech obrazovek
```

Struktura:

```
src/main.py              vstup aplikace
src/app/rules/dh.py      pravidla a tabulky Dračí Hlídky
src/app/rules/drd.py     pravidla a tabulky Dračího doupěte 1.6
src/app/model.py         postava, předměty, odvozené hodnoty
src/app/storage.py       ukládání v zařízení
src/app/core.py          navigace, dialogy, stav
src/app/ui/*.py          obrazovky
tests/                   testy (pravidla, proklikání všech obrazovek obou her)
```

## Co ověřit v příručkách

Tabulky ras, povolání, oprav, životů a startovní výbavy jsou přepsané z příruček. Následující body jsou
v aplikaci řešené rozumným výchozím nastavením a dají se upravit ručně:

- **DH – zranění v boji**: rozdíl útoku a obrany + zranění zbraně (vzorce ÚČ/OČ jsou z osobního deníku DH).
  Opakování hodu při šestce lze vypnout v Kostkách → Zbraň.
- **DH – mana** podle tabulek příručky (hraničář, kouzelník, klerik – přízeň, alchymista – suroviny).
- **DrD – magenergie** podle tabulek PPZ a PPP; alchymista od 10. úrovně destiluje magenergii sám (ručně).
- **DrD – smrt při 0 životech** pravidla výslovně neuvádějí; deník ukazuje „V ohrožení života“.
- **Alchymie z PPP** (pyrofor, theurg) zatím není v seznamu výroby – jen předměty z PPZ.
- **Nosnost a naložení**: podle Tabulky nosnosti (DrD 360 mn ± 30 mn za opravu SIL, 20 mn ≈ 1 kg; DH v librách)
  a násobků nosnosti (do 4×).
- **DrD – kvalita zbroje bez brnění je 1** (Tabulka kvality zbroje).
- **Katalog a kouzla**: čísla jsou přepsaná ze skenů pravidel, popisy kouzel a schopností jsou jen stručná
  připomenutí – podrobnosti vždy v pravidlech. Ceny jsou orientační (1 zl = 10 st = 100 md).
- Hodnoty krolla v tabulkách DrD byly čteny ze skenu (obratnost −4, inteligence −6, charisma −5, rozsah charismy 1–11).

Písma (Cinzel, IM Fell English SC, Alegreya Sans) mají licenci SIL Open Font License a stahují se při sestavení.
Bez nich aplikace použije výchozí písmo zařízení.

## Družina – propojení hráčů a PJ

Způsob propojení volí PJ při zakládání kampaně (`src/app/ui/propojeni.py`):

- **U stolu** (`src/app/stul.py`): telefon PJ spustí malý server v místní síti (port 47821), hráči na stejné
  Wi-Fi (nebo na hotspotu telefonu PJ) ho najdou tlačítkem *Hledat stůl* nebo zadají čtyřmístný kód stolu.
  Bez internetu a bez účtů, data jsou jen v telefonech u stolu. **Jen v aplikaci (Android, PC)** – prohlížeč
  spojení v místní síti z https stránky nepovolí, takže webová verze (iPhone) u stolu hrát neumí.
- **Vlastní server PJ**: každý PJ si průvodcem ve 4 krocích založí bezplatný Supabase (projekt Free),
  spustí skript databáze (`supabase/schema.sql`, v aplikaci zkopíruje tlačítko) a zapne
  *Allow anonymous sign-ins*. Aplikace server zamkne **klíčem PJ** (`DRAK-XXXX-XXXX`) – kampaně pak zakládá
  jen PJ a stejným klíčem se PJ přihlásí na dalším zařízení. Hráči dostanou pozvánku jako QR nebo odkaz
  (adresa serveru + publishable key + kód kampaně). Free projekt se po týdnu bez hraní uspí – aplikace to
  pozná a ukáže, jak ho probudit.
- **Server aplikace** (placený Supabase pro všechny) je zatím jen v nabídce jako „připravujeme“.

Do aplikace patří jen **Project URL a publishable key** – aplikace tajný klíč (`sb_secret_…`, service_role)
odmítne. Schéma verze 2 přidává schvalování hráčů (`members.status`), zámek kampaně, úpravy od PJ
(`adjustments`), tajné zprávy (`messages`), poznámky PJ (`gm_notes`) a vlastníka serveru (`claim_server`).
Skript jde spustit znovu i přes verzi 1. Starý projekt z `src/app/config.py` zůstává pro kampaně z verze 0.12.

Kdo co vidí: kampaň a členy jen přijatí členové (čekající hráč jen sebe); celý deník jen hráč a PJ; skryté hody,
poznámky PJ a úpravy jen PJ (úpravu a zprávu i hráč, kterému patří); obrázky nahrává jen PJ. Obsah příruček PJ
není v aplikaci ani v repozitáři – PJ si ho nahraje jako balíček (JSON) jen do svého zařízení.

Testy: `tests/test_sync.py` (falešný Supabase s pravidly jako ve schématu, stav stolu, skutečný server stolu
na 127.0.0.1), `tests/test_ui.py` (všechny obrazovky Stolu PJ, průvodce, přihlášení PJ klíčem, hráč).
