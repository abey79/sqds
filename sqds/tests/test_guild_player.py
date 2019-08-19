import itertools
import random

from sqds.models import Player, Guild, Unit, PlayerUnitGear, PlayerUnit
from sqds_seed.factories import PlayerFactory, PlayerUnitFactory, GuildFactory, \
    UnitFactory, SkillFactory, ZetaFactory, ModFactory


def test_guild_import(guild_data):
    assert Guild.objects.count() == 1
    guild = Guild.objects.all()[0]
    assert all([p.guild == guild for p in Player.objects.all()])
    assert Guild.objects.annotate_stats()[0].player_count == Player.objects.count()


def test_guild_import_with_guild_only(guild_data_no_player):
    assert Guild.objects.count() == 1
    assert Guild.objects.all()[0].name == 'PREPARE'
    assert Player.objects.count() == 0
    assert Guild.objects.annotate_stats()[0].player_count == 0


def test_guild_annotate_faction_gp(game_data):
    guild = GuildFactory()
    player = PlayerFactory(guild=guild)
    sep_units = list(Unit.objects.filter(categories__api_id='affiliation_separatist'))
    gr_units = list(Unit.objects.filter(categories__api_id='affiliation_republic'))

    sep_pus = [PlayerUnitFactory(player=player, unit=unit) for unit in random.sample(
        sep_units, 3)]
    gr_pus = [PlayerUnitFactory(player=player, unit=unit) for unit in random.sample(
        gr_units, 3)]
    qs = Guild.objects.annotate_faction_gp()

    assert qs[0].sep_gp == sum(pu.gp for pu in sep_pus)
    assert qs[0].gr_gp == sum(pu.gp for pu in gr_pus)


def test_player_annotate_stats_unit_count(db):
    player = PlayerFactory()

    PlayerUnitFactory(player=player, unit=UnitFactory(), rarity=7, gear=13)
    PlayerUnitFactory(player=player, unit=UnitFactory(), rarity=7, gear=12)
    PlayerUnitFactory(player=player, unit=UnitFactory(), rarity=6, gear=11)
    PlayerUnitFactory(player=player, unit=UnitFactory(), rarity=6, gear=10)

    qs = Player.objects.filter(pk=player.pk).annotate_stats()

    assert qs.count() == 1
    assert qs[0].unit_count == 4
    assert qs[0].g13_unit_count == 1
    assert qs[0].g12_unit_count == 1
    assert qs[0].g11_unit_count == 1
    assert qs[0].g10_unit_count == 1
    assert qs[0].seven_star_unit_count == 2


def test_player_annotate_stats_zeta_count(db):
    player = PlayerFactory()
    unit = UnitFactory()
    SkillFactory(unit=unit, is_zeta=True)
    skill = SkillFactory(unit=unit, is_zeta=True)
    SkillFactory(unit=unit, is_zeta=False)
    pu = PlayerUnitFactory(player=player, unit=unit)
    ZetaFactory(player_unit=pu, skill=skill)

    qs = Player.objects.filter(pk=player.pk).annotate_stats()

    assert qs.count() == 1
    assert qs[0].zeta_count == 1


def test_guild_annotate_stats_gear_count_consistency(guild_data):
    """
    In any case, the total number of g12 gear (left + right) should be equal to the
    total number of gear equipped on g12 toons + 6 times number of g13 toons
    """
    gear_count = PlayerUnitGear.objects.filter(player_unit__gear=12).count()
    gear_count += 6 * PlayerUnit.objects.filter(gear=13).count()

    qs = Guild.objects.annotate_stats()

    assert qs.count() == 1
    assert qs[0].right_hand_g12_gear_count + qs[0].left_hand_g12_gear_count == gear_count


def test_player_mod_stats(db):
    """
    We create a bunch of player units with defined speed
    """
    # 2nd mod is always the array
    toon_mod_speeds = [
        (5, 30, 4, 5, 1, 0),
        (6, 15, 15, 2, 5, 1),
        (None, 30, None, 14, 0, 1),
        (None, None, None, None, None, None),
        (None, 30, None, None, None, None),
        (24, 30, 27, 21, 2, 25),
        (16, 17, 18, 19, 20, 21),
    ]

    mod_count = sum(x is not None for x in itertools.chain(*toon_mod_speeds))
    mod_count_6dot = 0
    mod_count_speed_25 = sum(x is not None and 25 <= x and i % 6 != 1
                             for i, x in enumerate(itertools.chain(*toon_mod_speeds)))
    mod_count_speed_20 = sum(x is not None and 20 <= x < 25 and i % 6 != 1
                             for i, x in enumerate(itertools.chain(*toon_mod_speeds)))
    mod_count_speed_15 = sum(x is not None and 15 <= x < 20 and i % 6 != 1
                             for i, x in enumerate(itertools.chain(*toon_mod_speeds)))
    mod_count_speed_10 = sum(x is not None and 10 <= x < 15 and i % 6 != 1
                             for i, x in enumerate(itertools.chain(*toon_mod_speeds)))
    mod_total_speed_15plus = sum(
        x for i, x in enumerate(itertools.chain(*toon_mod_speeds))
        if x is not None and x >= 15 and i % 6 != 1)

    player = PlayerFactory()
    for mod_speeds in toon_mod_speeds:
        pu = PlayerUnitFactory(unit=UnitFactory(), player=player)
        for slot, speed in enumerate(mod_speeds):
            if speed is not None:
                ModFactory(player_unit=pu, slot=slot, speed=speed, pips=5)

    qs = Player.objects.filter(pk=player.pk).annotate_stats()

    assert qs.count() == 1
    assert qs[0].mod_count == mod_count
    assert qs[0].mod_count_6dot == mod_count_6dot
    assert qs[0].mod_count_speed_25 == mod_count_speed_25
    assert qs[0].mod_count_speed_20 == mod_count_speed_20
    assert qs[0].mod_count_speed_15 == mod_count_speed_15
    assert qs[0].mod_count_speed_10 == mod_count_speed_10
    assert qs[0].mod_total_speed_15plus == mod_total_speed_15plus


def test_player_mod_stats_6pips(db):
    toon_mod_pips = [
        (5, 5, 5, 5, 5, 5),
        (5, 6, 6, 6, 6, 6),
        (None, None, None, None, None, None),
        (None, 6, None, 5, None, 6),
        (None, 4, 4, 4, 6, 5),
        (1, 2, 3, 4, 5, 6),
    ]

    mod_count = sum(x is not None for x in itertools.chain(*toon_mod_pips))
    mod_count_6dot = sum(x is not None and x == 6
                         for x in itertools.chain(*toon_mod_pips))

    player = PlayerFactory()
    for mod_pips in toon_mod_pips:
        pu = PlayerUnitFactory(unit=UnitFactory(), player=player)
        for slot, pips in enumerate(mod_pips):
            if pips is not None:
                ModFactory(player_unit=pu, slot=slot, pips=pips)

    qs = Player.objects.filter(pk=player.pk).annotate_stats()

    assert qs.count() == 1
    assert qs[0].mod_count == mod_count
    assert qs[0].mod_count_6dot == mod_count_6dot


def test_annotate_stats_consistency(guild_data):
    """
    The stats returned for the guild should be consistent with the sum of the guild's
    player stats. We use the guild data from the data files.
    """
    stats = [
        # annotate_stat
        'gp_char',
        'gp_ship',
        'unit_count',
        'seven_star_unit_count',
        'g13_unit_count',
        'g12_unit_count',
        'g11_unit_count',
        'g10_unit_count',
        'zeta_count',
        'g12_gear_count',
        'right_hand_g12_gear_count',
        'left_hand_g12_gear_count',
        'mod_count',
        'mod_count_6dot',
        'mod_count_speed_25',
        'mod_count_speed_20',
        'mod_count_speed_15',
        'mod_count_speed_10',
        'mod_total_speed_15plus',

        # annotate_faction_gp
        'sep_gp',
        'gr_gp',
    ]

    guild = Guild.objects.annotate_stats().annotate_faction_gp()[0]
    players = Player.objects.annotate_stats().annotate_faction_gp()

    for stat in stats:
        assert getattr(guild, stat) != 0  # We want actual data
        assert getattr(guild, stat) == sum(getattr(p, stat) for p in players)
