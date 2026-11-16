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


def test_weapon_combinations():
    from app.rules import drd_vybava
    items = {i["name"]: i for i in drd_vybava.catalog("Člověk")}
    two = items["Dvě šavle"]
    assert (two["attack"], two["damage"], two["defense"]) == (8, -2, 3)
    assert two["weight_mn"] == 50 and two["price"] == "64 zl"  # součet dvou šavlí
    assert items["Krátký meč a dýka"]["defense"] == 3
    assert len([i for i in items.values() if "kombinace" in i["info"]]) == 6


def _drd(race, cls, attrs, items=()):
    from app import model
    c = model.create_character("drd", "T", race, cls, list(attrs))
    c["items"] = [model.item(n, cat, equipped=True, **st) for n, cat, st in items]
    return c


def test_rule_examples_kram_whush_sipka():
    """Příklady z PPZ s. 68 a 72: ÚČ a OČ."""
    from app import model
    kram = _drd("Elf", "Válečník", [16, 11, 12, 10, 10],
                [("Široký meč", "Zbraň", {"attack": 5, "damage": 0, "defense": 0}),
                 ("Šupinová zbroj", "Zbroj", {"quality": 4})])
    assert model.uc(kram, model.weapons(kram)[0]) == 7
    assert model.oc_sheet(kram) == 4
    whush = _drd("Elf", "Válečník", [14, 16, 12, 10, 10], [("Šupinová zbroj", "Zbroj", {"quality": 4})])
    assert model.oc_sheet(whush) == 6
    sipka = _drd("Elf", "Zloděj", [7, 14, 10, 10, 12], [("Široký meč", "Zbraň", {"attack": 5, "damage": 0, "defense": 0})])
    assert model.uc(sipka, model.weapons(sipka)[0]) == 3


def test_racial_weapon_and_unarmed():
    from app import model
    human = _drd("Člověk", "Válečník", [16, 11, 12, 10, 10],
                 [("Široký meč", "Zbraň", {"attack": 5, "damage": 0, "defense": 0})])
    assert model.is_racial(human, model.weapons(human)[0])
    assert model.uc(human, model.weapons(human)[0]) == 8  # 7 + rodová zbraň
    bare = _drd("Člověk", "Kouzelník", [10, 10, 10, 16, 14])
    w = model.weapons(bare)[0]
    assert w["defense"] == -3 and model.oc_sheet(bare) == 1 and model.oc(bare, w) == -2
    bare["items"] = [model.item("Štít", "Štít", equipped=True, defense=1)]
    assert model.weapons(bare)[0]["defense"] == 0  # se samotným štítem obrana zbraně 0
    clumsy = _drd("Kroll", "Válečník", [18, 5, 18, 5, 5])
    assert model.oc_sheet(clumsy) == 0  # OČ nikdy pod nulu


def test_backup_roundtrip(make_app):
    import asyncio
    from app import model
    from app.ui import backup
    app, page = make_app()
    c = model.create_character("drd", "Záloha", "Elf", "Kouzelník", [10, 12, 10, 16, 14])
    app.add_character(c)
    ref = asyncio.run(app.store.save_image("x1", b"PNGDATA"))
    c["avatar"] = ref
    raw = asyncio.run(backup.build_backup(app))
    data = backup.parse_backup(raw)
    assert data["chars"][0]["name"] == "Záloha" and data["images"]
    app2, page2 = make_app()
    n = asyncio.run(backup.restore(app2, data))
    assert n == 1 and app2.order == [c["id"]]
    new_ref = app2.chars[c["id"]]["avatar"]
    assert asyncio.run(app2.store.load_image(new_ref)) == b"PNGDATA"
    import pytest
    with pytest.raises(ValueError):
        backup.parse_backup(b'{"foo": 1}')


def test_shrink_image():
    import io
    from PIL import Image
    from app.core import shrink_image
    buf = io.BytesIO()
    Image.new("RGB", (3000, 2000), (200, 30, 30)).save(buf, "PNG")
    out = shrink_image(buf.getvalue(), 512)
    im = Image.open(io.BytesIO(out))
    assert max(im.size) == 512 and len(out) < len(buf.getvalue())
    assert shrink_image(b"not an image") == b"not an image"


def test_fitness_and_size_tables():
    # PPZ s. 71: kudůk ODL 13, 7 životů → mez 1, postih −1 při 2 životech; 12 životů → mez 2
    assert drd.knockout_limit(7, 13) == 1 and drd.knockout_limit(12, 13) == 2
    assert drd.wound_penalty(2, 7, 13) == -1 and drd.wound_penalty(4, 12, 13) == 0 and drd.wound_penalty(3, 12, 13) == -1
    assert drd.knockout_limit(20, 20) == 1 and drd.wound_penalty(1, 20, 20) == 0
    assert drd.size_mod("A", "E") == -4 and drd.size_mod("E", "A") == -1  # trpaslík proti drakovi
    assert drd.ranged_size_mod("D") == 1


def test_pct_outcomes():
    assert drd.pct_outcome(40, 30, 1) == (False, "fatální neúspěch")
    assert drd.pct_outcome(100, 30, 1) == (False, "fatální neúspěch")
    assert drd.pct_outcome(35, 30, 1) == (False, None)
    assert drd.pct_outcome(20, 52, 6) == (True, "totální úspěch")
    assert drd.pct_outcome(20, 52, 5) == (True, None)


def test_xp_tables_and_movement():
    assert drd.xp_for_level("Kouzelník", 6) == 10750 and drd.training_cost("Zloděj", 5) == 12
    assert drd.xp_for_level("Hraničář", 7) == 16350 and drd.training_cost("Kouzelník", 16) == 144
    assert drd.level_for_xp("Válečník", 900) == 3
    assert drd.base_movement("Barbar", [19, 9, 10, 10, 10]) == 19  # PPZ s. 83, Hrun
    assert drd.movement("Barbar", [19, 9, 10, 10, 10], 3.5) == 5
    assert drd.perception("Hobit", [10, 10, 10, 13, 10]) == (13, 11)  # PPZ s. 86, Fergo
    assert drd.HP_FIXED["Válečník"] == 2 and drd.HP_FIXED["Zloděj"] == 1


def test_dh_tables():
    from app.rules import dh
    assert dh.class_mana("Kouzelník", 1, [5, 5, 5, 10, 5]) == 5
    assert dh.class_mana("Klerik", 6, [5, 5, 5, 5, 23]) == 41
    assert dh.class_mana("Hraničář", 3, [5, 5, 5, 14, 5]) == 12
    assert dh.class_mana("Alchymista", 1, [5, 14, 5, 5, 5]) == 100 and dh.alch_start_raw([5, 14, 5, 5, 5]) == 200
    assert dh.xp_for_level(6) == 8500 and dh.level_for_xp(4400) == 5
    assert dh.attr_up_level(3) and not dh.attr_up_level(4)
    k, gain = dh.level_hp_roll([5, 5, 2, 5, 5], fixed=True)
    assert k == 3 and gain == 1  # 3 + (−4) → nejméně 1
    assert dh.fatigue_limit([5, 5, 18, 5, 5]) == 14 and dh.fatigue_state(15, [5, 5, 18, 5, 5]) == ("Unavený", -3)
    assert dh.movement("Obr", [10, 10, 10, 5, 5]) == 40


def test_gear_restrictions():
    from app import model
    from app.rules import drd_vybava
    assert drd_vybava.gear_problem("Kouzelník", {"name": "Dlouhý luk", "category": "Zbraň"})
    assert drd_vybava.gear_problem("Kouzelník", {"name": "Dýka", "category": "Zbraň"}) is None
    assert drd_vybava.gear_problem("Zloděj", {"name": "Kroužková zbroj", "category": "Zbroj"})
    assert drd_vybava.gear_problem("Hraničář", {"name": "Těžká kuše", "category": "Zbraň"})
    assert drd_vybava.gear_problem("Válečník", {"name": "Obouruční meč", "category": "Zbraň"}) is None
    c = model.create_character("drd", "W", "Člověk", "Válečník", [16, 12, 15, 10, 10])
    c["items"] = [model.item("Obouruční meč", "Zbraň", equipped=True, attack=7, damage=1, defense=-1, hands=2),
                  model.item("Štít", "Štít", equipped=True, defense=1)]
    w = model.weapons(c)[0]
    assert model.oc(c, w) == model.oc_sheet(c) - 1  # se štítem bez bonusu
    assert any("štít" in x for x in model.warnings(c))
