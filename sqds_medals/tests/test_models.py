from sqds.models import Player, Guild, Unit, Skill
from sqds_medals.models import Medal
from sqds_seed.factories import StatMedalRuleFactory, ZetaMedalRuleFactory, UnitFactory, \
    SkillFactory


def test_stat_medal_rule_str(db):
    rule = StatMedalRuleFactory(unit=UnitFactory(), stat='health', value=10000)
    assert str(rule) == 'StatMedalRule: Health ≥ 10000'


def test_zeta_medal_rule_str(db):
    unit = UnitFactory()
    skill = SkillFactory(unit=unit, is_zeta=True)
    rule = ZetaMedalRuleFactory(unit=UnitFactory(), skill=skill)
    assert str(rule) == 'ZetaMedalRule: ' + skill.name


def test_annotate_stats_medal_count_consistency(guild_data):
    bossk = Unit.objects.get(api_id='BOSSK')
    bossk_zeta_skills = Skill.objects.filter(unit=bossk, is_zeta=True)

    assert bossk_zeta_skills.count() == 2

    StatMedalRuleFactory(unit=bossk, stat='health', value=1000)
    StatMedalRuleFactory(unit=bossk, stat='health', value=100000)
    StatMedalRuleFactory(unit=bossk, stat='gear', value=12)
    StatMedalRuleFactory(unit=bossk, stat='gear', value=4)
    StatMedalRuleFactory(unit=bossk, stat='protection', value=1000)
    ZetaMedalRuleFactory(unit=bossk, skill=bossk_zeta_skills[0])
    ZetaMedalRuleFactory(unit=bossk, skill=bossk_zeta_skills[1])

    Medal.objects.update_all()

    guild = Guild.objects.annotate_stats().annotate_faction_gp()[0]
    players = Player.objects.annotate_stats().annotate_faction_gp()

    assert guild.medal_count != 0
    assert guild.medal_count == sum(p.medal_count for p in players)
