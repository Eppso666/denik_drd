import random

from app.rules import dh, drd
from app.rules.common import open_d6


def test_dh_bonus_table():
    expected = {1: -5, 2: -4, 3: -4, 4: -3, 5: -3, 6: -2, 7: -2, 8: -1, 9: -1, 10: 0, 11: 0, 12: 1, 13: 1,
                14: 2, 15: 2, 16: 3, 17: 3, 18: 4, 19: 4, 20: 5, 21: 5, 22: 6, 23: 6}
    for v, b in expected.items():
        assert dh.bonus(v) == b, v


def test_dh_example_from_rulebook():
    # Příklad tvorby postavy: trpaslík válečník, hody 5,4,6,5,2 → 18/9/19/10/7, opravy +4/−1/+4/0/−2
    attrs = dh.finalize([5, 4, 6, 5, 2], "Trpaslík", "Válečník")
    assert attrs == [18, 9, 19, 10, 7]
    assert [dh.bonus(a) for a in attrs] == [4, -1, 4, 0, -2]
    assert dh.hit_points(attrs) == 14
    assert dh.death_threshold(attrs) == -14


def test_dh_auto_generation_ranges():
    rng = random.Random(1)
    for race in dh.RACES:
        for cls in dh.CLASSES:
            a = dh.generate_auto(race, cls, rng)
            for i, v in enumerate(a):
                base = dh.RACES[race][i] + (3 if dh.ATTRS[i] in dh.CLASSES[cls] else 0)
                assert base + 1 <= v <= base + 6


def test_dh_check_must_exceed():
    class R:
        def randint(self, a, b):
            return 5
    k, total, ok = dh.check(2, 3, 10, rng=R())
    assert (k, total, ok) == (5, 10, False)  # rovná se obtížnosti → neúspěch
    _, total, ok = dh.check(2, 3, 10, adv=1, rng=R())
    assert total == 15 and ok


def test_drd_bonus_table():
    expected = {1: -5, 2: -4, 3: -4, 5: -3, 7: -2, 9: -1, 10: 0, 12: 0, 13: 1, 14: 1, 15: 2, 17: 3, 18: 3, 19: 4,
                20: 4, 21: 5}
    for v, b in expected.items():
        assert drd.bonus(v) == b, v


def test_drd_ranges_from_rulebook():
    assert drd.range_dice(6, 16) == (2, 4)       # 2k6+4
    assert drd.range_dice(1, 6) == (1, 0)        # 1k6
    assert drd.range_dice(4, 19) == (3, 1)       # 3k6+1
    assert drd.attr_range("Barbar", "Válečník", 0) == (14, 19)
    assert drd.attr_range("Elf", "Alchymista", 2) == (8, 13)
    assert drd.attr_range("Barbar", "Válečník", 4) == (1, 16)


def test_drd_generation_within_ranges():
    rng = random.Random(3)
    for race in drd.RACE_RANGES:
        for cls in drd.CLASSES:
            a = drd.generate_auto(race, cls, rng)
            for i, v in enumerate(a):
                lo, hi = drd.attr_range(race, cls, i)
                assert lo <= v <= hi


def test_drd_hp_and_level():
    assert drd.hit_points("Válečník", [16, 8, 15, 10, 5]) == 12
    rng = random.Random(0)
    for _ in range(50):
        _, gain = drd.level_hp_roll("Kouzelník", [10, 10, 2, 15, 15], rng)
        assert gain >= 1


def test_wounds_and_trap():
    assert drd.wound(12, 12, 3) == 0
    assert drd.wound(13, 12, 3) == 4
    assert drd.wound(13, 12, -5) == 1
    assert dh.wound(10, 7, 1) == 4

    class R:
        def randint(self, a, b):
            return 4
    assert drd.trap(2, 6, rng=R()) == (4, 6, True)
    assert drd.trap(1, 6, rng=R()) == (4, 5, False)


def test_open_d6():
    seq = iter([6, 6, 2])

    class R:
        def randint(self, a, b):
            return next(seq)
    assert open_d6(R()) == [6, 6, 2]


def test_drd_thief_and_ranger_abilities():
    attrs = [10, 16, 10, 10, 15]  # OBR +2, CHA +2
    ab = {a["name"]: a for a in drd.class_abilities("Zloděj", 1, attrs)}
    assert len(ab) == 11
    assert ab["Převleky"]["pct"] == 5 + 3 * 2
    assert ab["Vybírání kapes"]["pct"] == 10 + 2 + 2
    assert drd.class_abilities("Zloděj", 9, attrs)[0]["pct"] == 25 + 6  # nad 5. úrovní platí hodnoty pro 5.
    ranger = {a["name"]: a for a in drd.class_abilities("Hraničář", 4, attrs)}
    assert ranger["Stopování – volná příroda"]["pct"] == 88
    assert ranger["Mimosmyslové schopnosti"]["locked"] is False
    assert {a["name"]: a for a in drd.class_abilities("Hraničář", 1, attrs)}["Mimosmyslové schopnosti"]["locked"]
    for cls in drd.CLASSES:
        assert drd.class_abilities(cls, 1, attrs)
    assert "k4" in drd.DICE and "k20" in drd.DICE


def test_wizard_tables():
    from app.rules import drd_kouzla
    assert drd_kouzla.wizard_mana(1, 17) == 8 and drd_kouzla.wizard_mana(5, 21) == 31
    assert drd_kouzla.wizard_mana(6, 8) == 19 and drd_kouzla.wizard_mana(15, 20) == 91
    assert drd_kouzla.spell_count(1) == 3 and drd_kouzla.spell_count(15) == 46
    assert drd_kouzla.success_chance(17) == 85 and drd_kouzla.success_chance(9) == 32
    assert len([s for s in drd_kouzla.SPELLS if s["source"] == "PPZ"]) == 27
    assert len([s for s in drd_kouzla.SPELLS if s["source"] == "PPP"]) == 49


def test_branch_abilities_and_thief_tables():
    a = drd.class_abilities("Zloděj", 6, [10, 12, 10, 10, 12], "Lupič")
    pre = next(x for x in a if x["name"] == "Převleky")
    assert pre["pct"] == 28  # bonus CHA 12 = 0
    a = drd.class_abilities("Válečník", 9, [16, 12, 15, 10, 10], "Bojovník")
    names = {x["name"]: x["locked"] for x in a}
    assert names["Drtivost"] is False and names["Vícenásobné útoky"] is True


def test_capacity_rules():
    from app import model
    from app.rules import drd_vybava, dh_vybava
    assert drd_vybava.carry_capacity_mn(0) == 360 and drd_vybava.carry_capacity_mn(4) == 480
    assert dh_vybava.carry_capacity(0) == 15 and dh_vybava.carry_capacity(6) == 28
    c = model.create_character("drd", "X", "Barbar", "Válečník", [19, 9, 15, 10, 5])
    assert c["capacity"] == 24.0  # 480 mn


def test_branch_mana_tables():
    a = [10, 14, 12, 13, 10]  # OBR 14, INT 13
    assert drd.class_mana("Hraničář", 5, a) == 14
    assert drd.class_mana("Hraničář", 6, a) == 14  # bez oboru zůstává 5. úroveň
    assert drd.class_mana("Hraničář", 6, a, "Druid") == 20
    assert drd.class_mana("Hraničář", 15, a, "Chodec") == 49
    assert drd.class_mana("Alchymista", 6, a, "Pyrofor") == 230
    assert drd.class_mana("Alchymista", 12, a, "Theurg") == 600
    assert drd.class_mana("Kouzelník", 6, a, "Mág") == 26
    assert drd.class_mana("Válečník", 6, a, "Bojovník") is None
