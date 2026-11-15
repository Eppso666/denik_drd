# Deník dobrodruha

Mobilní deník postavy pro **Dračí Hlídku** a **Dračí doupě 1.6**. Napsáno v Pythonu (Flet 1.1).
Android dostane instalační soubor `.apk`, iPhone webovou verzi, kterou si přidá na plochu jako aplikaci.

## Co aplikace umí (verze 0.1)

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
- **Vlastní dovednosti** (DH: vlastnost + stupeň; DrD: šance v %).
- **Batoh**: předměty, výbava na těle, peníze, **naložení automaticky z vah nebo ručně**, nosnost.
- **Kostky**: výběr dovednosti / zbraně / schopnosti / pasti, na kterou házíš, a volné hody.
- **Souboj**: soupeř z bestiáře nebo vlastní, útok, obrana, zranění, iniciativa, průběh kol.
- **Bestiář** zvlášť pro každou hru (DrD v klasickém zápisu: životaschopnost, útok, obrana, …), s obrázkem.
- **Deník**: poznámky se štítky a připnutím, **obrázky** (mapy, portréty) z fotoaparátu nebo galerie.
- Vše se ukládá **jen v zařízení**. Družina a sdílení přes Supabase přijdou v další verzi.

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
- **DH – mana** jednotlivých povolání a přírůstek životů při postupu: zadávají se ručně.
- **DrD – magenergie** a zkušenosti na další úroveň: zadávají se ručně.
- **Nosnost**: výchozí hodnota je orientační, nastav ji v Batohu podle pravidel.
- Hodnoty krolla v tabulkách DrD byly čteny ze skenu (obratnost −4, inteligence −6, charisma −5, rozsah charismy 1–11).

Písma (Cinzel, IM Fell English SC, Alegreya Sans) mají licenci SIL Open Font License a stahují se při sestavení.
Bez nich aplikace použije výchozí písmo zařízení.
