"""Číselné účinky kouzel DrD 1.6 po úspěšném seslání – kostky zranění, léčení a zásahu.

Jen čísla z pravidel (PPZ, PPP), žádné texty. Ověřeno podle přepisu příruček 25. 11. 2026.
Klíče: kind (zranění / léčení / zabití), dice (počet, stěny, přičíst), per (za co se hází),
first / next (magy za první a každý další blesk či kus), hit (šance na zásah v %, hází se jednou za cíl).
"""
from __future__ import annotations

EFFECTS: dict[str, dict] = {
    # kouzelník – Pravidla pro začátečníky
    "Modré blesky": {"kind": "zranění", "dice": (1, 6, 0), "per": "blesk", "first": 3, "next": 2},
    "Zelené blesky": {"kind": "zranění", "dice": (2, 6, 0), "per": "blesk", "first": 4, "next": 3, "hit": 80},
    "Nebezpečné ovoce": {"kind": "zranění", "dice": (1, 6, 4), "per": "kus", "first": 3, "next": 3,
                         "note": "Výbuch hrušky – hoď, až vybuchne (sama vybuchne po 5–10 směnách)."},
    "Ohnivý déšť": {"kind": "zranění", "dice": (1, 6, 0), "per": "sáh",
                    "note": "Za každý čtvereční sáh terče (člověk 1, kůň 3, drak 50)."},
    # kouzelník – Pravidla pro pokročilé
    "Bílý blesk": {"kind": "zranění", "dice": (1, 6, 0), "per": None},
    "Černý blesk": {"kind": "zranění", "dice": (3, 6, 38), "per": None},
    "Žluté blesky": {"kind": "zranění", "dice": (3, 6, 0), "per": "blesk", "first": 5, "next": 4, "hit": 72},
    "Fialové blesky": {"kind": "zranění", "dice": (4, 6, 0), "per": "blesk", "first": 6, "next": 5, "hit": 68,
                       "note": "Až na tři tvory, magenergie pro každého zvlášť; za každý další cíl zásah −1 %."},
    "Rudé blesky": {"kind": "zranění", "dice": (5, 6, 0), "per": "blesk", "first": 7, "next": 6, "hit": 66,
                    "note": "Za každý další cíl zásah −1 %."},
    "Zabij": {"kind": "zabití", "dice": (4, 10, 0), "per": None,
              "note": "Celková životaschopnost zabitých tvorů (od nejslabších)."},
    # hraničář
    "Uzdrav lehká zranění": {"kind": "léčení", "dice": (1, 6, 1), "per": None},
    "Uzdrav těžká zranění": {"kind": "léčení", "dice": (2, 6, 2), "per": None},
    "Ošetři zranění chladem": {"kind": "léčení", "dice": (1, 6, 14), "per": None},
    "Ošetři zranění kyselinou": {"kind": "léčení", "dice": (1, 6, 10), "per": None},
    "Ošetři zranění ohněm": {"kind": "léčení", "dice": (1, 6, 16), "per": None},
}


def effect(name: str) -> dict | None:
    return EFFECTS.get(name)


def count(name: str, mana: int) -> int:
    """Kolik blesků / kusů dá vložená magenergie (u ostatních 1)."""
    e = EFFECTS.get(name) or {}
    if e.get("per") not in ("blesk", "kus") or not e.get("first"):
        return 1
    if mana < e["first"]:
        return 0
    return 1 + (mana - e["first"]) // e["next"]


def dice_label(dice: tuple[int, int, int], times: int = 1) -> str:
    n, sides, add = dice
    base = f"{n if n > 1 else ''}k{sides}" + (f"+{add}" if add else "")
    return base if times == 1 else f"{times} × {base}"


def summary(name: str, mana: int) -> str | None:
    """Přepočet do formuláře seslání, např. „7 magů = 3 blesky · zranění 3 × k6“."""
    e = EFFECTS.get(name)
    if not e:
        return None
    n = count(name, mana)
    if e.get("per") in ("blesk", "kus"):
        word = {"blesk": ("blesk", "blesky", "blesků"), "kus": ("kus", "kusy", "kusů")}[e["per"]]
        w = word[0] if n == 1 else (word[1] if 1 < n < 5 else word[2])
        head = f"{mana} magů = {n} {w}" if n else f"Na první {e['per']} je třeba {e['first']} magů"
        if not n:
            return head
        return head + f" · {e['kind']} {dice_label(e['dice'], n)}" + (f" · zásah {e['hit']} %" if e.get("hit") else "")
    return f"{e['kind'].capitalize()} {dice_label(e['dice'])}" + (" za každý čtvereční sáh" if e.get("per") == "sáh" else "")
