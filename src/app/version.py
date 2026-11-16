"""Číslo verze a novinky, které se po aktualizaci ukážou na úvodní obrazovce."""
from __future__ import annotations

VERSION = "0.9.0"

CHANGES: dict[str, list[str]] = {
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
