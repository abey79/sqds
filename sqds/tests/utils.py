import random

from sqds.models import Unit, PlayerUnitGear, Gear, Skill
from sqds_seed.factories import CategoryFactory, GearFactory, UnitFactory, GuildFactory, \
    PlayerFactory, PlayerUnitFactory, ZetaFactory, ModFactory


def random_sublist(lst, probability=0.5):
    """
    Returns an iterator that includes each element of lst with a given probability.
    :param  lst Starting list
    :param  probability Probability of inclusion of each of lst elements
    """
    return filter(lambda _: random.random() < probability, lst)


def generate_game_data():
    """
    Generate random mock game data.
    """
    categories = CategoryFactory.create_batch(5)
    GearFactory.create_batch(30)
    for _ in range(15):
        UnitFactory(categories=random_sublist(categories, 0.1))


def generate_guild(player_count=45):
    """
    Generate a mock guild.
    """
    guild = GuildFactory()
    for idx in range(player_count):
        player = PlayerFactory(guild=guild)

        # Generate some random player units
        for unit in random_sublist(Unit.objects.all(), 0.85):
            player_unit = PlayerUnitFactory(
                player=player, unit=unit)

            # Generate some gear
            for _ in range(random.randint(0, 5)):
                PlayerUnitGear(player_unit=player_unit,
                               gear=random.choice(Gear.objects.all()))

            # Zeta some abilities
            for skill in Skill.objects.filter(unit=unit):
                if skill.is_zeta and random.random() > 0.5:
                    ZetaFactory(player_unit=player_unit,
                                skill=skill)

            # Equip some mods
            for slot in random_sublist(range(7)):
                ModFactory(player_unit=player_unit, slot=slot)