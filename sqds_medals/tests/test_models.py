from sqds.models import Player, Guild, Unit, Skill
from sqds_medals.models import Medal, StatMedalRule
from sqds_seed.factories import (
    StatMedalRuleFactory,
    ZetaMedalRuleFactory,
    UnitFactory,
    SkillFactory,
    PlayerUnitFactory,
    PlayerFactory,
)


def test_stat_medal_rule_str_repr(db):
    unit = UnitFactory()
    rule = StatMedalRuleFactory(unit=unit, stat="health", value=10000)

    assert "Health" in str(rule)
    assert str(10000) in str(rule)

    assert "health" in repr(rule)
    assert str(1000) in repr(rule)
    assert unit.name in repr(rule)
    assert "StatMedalRule" in repr(rule)


def test_zeta_medal_rule_str(db):
    unit = UnitFactory()
    skill = SkillFactory(unit=unit, is_zeta=True)
    rule = ZetaMedalRuleFactory(unit=unit, skill=skill)

    assert "Zeta" in str(rule)
    assert skill.name in str(rule)

    assert "ZetaMedalRule" in repr(rule)
    assert skill.name in repr(rule)
    assert unit.name in repr(rule)


def test_unit_is_medaled_ok(medaled_unit):
    assert medaled_unit.is_medaled()


def test_unit_is_medaled_over_under(under_medaled_unit, over_medaled_unit):
    assert not under_medaled_unit.is_medaled()
    assert not over_medaled_unit.is_medaled()


def test_update_all_with_ally_code(db):
    """
    Medals should not be created for player unit belonging to players whose ally code
    are not passed to MedalManager.update_all()
    """
    unit = UnitFactory()
    for x in range(7):
        StatMedalRuleFactory(unit=unit, stat="health", value=x * 1000)

    p1, p2 = PlayerFactory.create_batch(2)
    PlayerUnitFactory(player=p1, unit=unit, health=3500)
    pu2 = PlayerUnitFactory(player=p2, unit=unit, health=3500)

    Medal.objects.update_all(ally_codes=[p1.ally_code])
    assert Medal.objects.count() == 4
    assert Medal.objects.filter(player_unit=pu2).count() == 0

    Medal.objects.update_all()
    assert Medal.objects.count() == 8


def test_update_for_unit(db):
    unit1, unit2 = UnitFactory.create_batch(2)
    for x in range(7):
        for unit in unit1, unit2:
            StatMedalRuleFactory(unit=unit, stat="health", value=x * 1000)
    player = PlayerFactory()
    PlayerUnitFactory(player=player, unit=unit1, health=3500)
    pu2 = PlayerUnitFactory(player=player, unit=unit2, health=3500)

    Medal.objects.update_for_unit(unit=unit1)
    assert Medal.objects.count() == 4
    assert Medal.objects.filter(player_unit=pu2).count() == 0

    Medal.objects.update_all()
    assert Medal.objects.count() == 8

    StatMedalRule.objects.filter(unit=unit1)[0].delete()
    StatMedalRule.objects.filter(unit=unit2)[0].delete()
    Medal.objects.update_for_unit(unit1)
    assert Medal.objects.count() == 3  # because of delete propagation
    assert Medal.objects.filter(player_unit=pu2).count() == 3

    Medal.objects.update_all()
    assert Medal.objects.count() == 0


def test_update_for_unit_after_rule_removal(db):
    unit = UnitFactory()
    rules = [
        StatMedalRuleFactory(unit=unit, stat="health", value=x * 1000) for x in range(7)
    ]
    player = PlayerFactory()
    PlayerUnitFactory(player=player, unit=unit, health=3500)

    assert Medal.objects.count() == 0
    Medal.objects.update_for_unit(unit)
    assert Medal.objects.count() == 4
    rules[0].delete()
    Medal.objects.update_for_unit(unit)
    assert Medal.objects.count() == 0


def test_update_all_deletes_invalid_medals(db):
    unit = UnitFactory()
    PlayerUnitFactory(unit=unit, player=PlayerFactory(), health=3500)
    rules = [
        StatMedalRuleFactory(unit=unit, stat="health", value=x * 1000) for x in range(7)
    ]

    Medal.objects.update_all()
    assert Medal.objects.count() == 4
    rules[0].delete()
    Medal.objects.update_all()
    assert Medal.objects.count() == 0


def test_annotate_stats_medal_count_consistency(guild_data):
    bossk = Unit.objects.get(api_id="BOSSK")
    bossk_zeta_skills = Skill.objects.filter(unit=bossk, is_zeta=True)

    assert bossk_zeta_skills.count() == 2

    StatMedalRuleFactory(unit=bossk, stat="health", value=1000)
    StatMedalRuleFactory(unit=bossk, stat="health", value=100000)
    StatMedalRuleFactory(unit=bossk, stat="gear", value=12)
    StatMedalRuleFactory(unit=bossk, stat="gear", value=4)
    StatMedalRuleFactory(unit=bossk, stat="protection", value=1000)
    ZetaMedalRuleFactory(unit=bossk, skill=bossk_zeta_skills[0])
    ZetaMedalRuleFactory(unit=bossk, skill=bossk_zeta_skills[1])

    Medal.objects.update_all()

    guild = Guild.objects.annotate_stats().annotate_faction_gp()[0]
    players = Player.objects.annotate_stats().annotate_faction_gp()

    assert guild.medal_count != 0
    assert guild.medal_count == sum(p.medal_count for p in players)
