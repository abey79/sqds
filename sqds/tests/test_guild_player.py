import datetime
import itertools
import random

from django.utils import timezone

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


def test_player_import_multiple(game_data, patched_swgoh):
    ally_codes = [168562452, 278732538, 772324267]
    imported_players = Player.objects.update_or_create_multiple_from_swgoh(ally_codes)

    assert len(imported_players) == 3

    players = Player.objects.all()

    assert set(players) == set(imported_players)
    assert set(ally_codes) == {p.ally_code for p in players}


def test_player_import_single(game_data, patched_swgoh):
    ally_code = 168562452
    imported_player = Player.objects.update_or_create_from_swgoh(ally_code)
    players = Player.objects.all()

    assert players.count() == 1
    assert players[0] == imported_player
    assert players[0].ally_code == ally_code


def test_player_set_ensure_exists_single(game_data, patched_swgoh, mocker):
    ally_code = 868797936
    player, = Player.objects.ensure_exist(ally_code)
    assert patched_swgoh['get_player_data_batch'].call_count == 1

    new_name = 'Stoopid name'
    old_name = player.name
    player.name = new_name
    player.save()
    player, = Player.objects.ensure_exist(ally_code, max_days=1)
    assert patched_swgoh['get_player_data_batch'].call_count == 1
    assert player.name == new_name

    now = timezone.now()
    mocker.patch('django.utils.timezone.now',
                 return_value=now + datetime.timedelta(days=2))
    player, = Player.objects.ensure_exist(ally_code, max_days=1)
    assert patched_swgoh['get_player_data_batch'].call_count == 2
    assert player.name == old_name


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


def test_player_unit_annotate_stats(db):
    pass


def test_player_dict_from_ally_code_all_units(db):
    player = PlayerFactory()
    units = UnitFactory.create_batch(3)
    for u in units:
        PlayerUnitFactory(player=player, unit=u)

    dct = PlayerUnit.objects.dict_from_ally_code(player.ally_code)

    assert dct.keys() == set(u.api_id for u in units)

    attr_list = [
        # PlayerUnit fields
        'gp', 'rarity', 'level', 'gear', 'equipped_count', 'speed', 'health',
        'protection', 'physical_damage', 'physical_crit_chance', 'special_damage',
        'special_crit_chance', 'crit_damage', 'potency', 'tenacity', 'armor',
        'resistance', 'armor_penetration', 'resistance_penetration', 'health_steal',
        'accuracy', 'mod_speed', 'mod_health', 'mod_protection', 'mod_physical_damage',
        'mod_special_damage', 'mod_physical_crit_chance', 'mod_special_crit_chance',
        'mod_crit_damage', 'mod_potency', 'mod_tenacity', 'mod_armor', 'mod_resistance',
        'mod_critical_avoidance', 'mod_accuracy', 'last_updated',

        # annotate_stats
        'mod_speed_no_set', 'zeta_count',
    ]

    for api_id in dct:
        pu = PlayerUnit.objects.annotate_stats().get(unit__api_id=api_id)
        for attr in attr_list:
            assert getattr(dct[api_id], attr) == getattr(pu, attr)

        # dict_from_ally_code
        assert dct[api_id].unit_name == pu.unit.name
        assert dct[api_id].unit_api_id == pu.unit.api_id == api_id
        assert dct[api_id].player_name == pu.player.name == player.name
        assert dct[api_id].player_ally_code == pu.player.ally_code == player.ally_code


def test_player_dict_from_ally_code_some_units(db):
    player = PlayerFactory()
    units = UnitFactory.create_batch(3)
    for u in units:
        PlayerUnitFactory(player=player, unit=u)

    unit_ids = [units[0].api_id, units[2].api_id]
    dct = PlayerUnit.objects.dict_from_ally_code(player.ally_code, unit_ids)
    assert dct.keys() == set(unit_ids)
