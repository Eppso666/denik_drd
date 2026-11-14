"""Společné pomůcky pro hody kostkou."""
from __future__ import annotations

import random

RNG = random.Random()


def d(sides: int, rng: random.Random | None = None) -> int:
    """Jeden hod kostkou k`sides`."""
    return (rng or RNG).randint(1, sides)


def open_d6(rng: random.Random | None = None, cap: int = 20) -> list[int]:
    """Hod k6+: při šestce se hází znovu a výsledky se sčítají."""
    rolls: list[int] = []
    while True:
        v = d(6, rng)
        rolls.append(v)
        if v != 6 or len(rolls) >= cap:
            return rolls


def fmt(b: int) -> str:
    """Formát opravy: +2, −1, 0."""
    if b > 0:
        return f"+{b}"
    if b < 0:
        return f"−{-b}"
    return "0"


def roll_expr(rolls: list[int]) -> str:
    return "+".join(str(r) for r in rolls)
