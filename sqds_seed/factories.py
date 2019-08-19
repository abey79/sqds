import random

import factory.fuzzy
from faker.providers import BaseProvider

from sqds.models import Category, Unit, Skill, Gear, Guild, Player, PlayerUnit, Zeta, \
    PlayerUnitGear, Mod, ModSet


# noinspection PyMethodMayBeStatic
class SqdsProvider(BaseProvider):
    def ally_code(self):
        return (random.randint(100, 999)
                + random.randint(100, 999) * 1000
                + random.randint(100, 999) * 1000000)

    def gaussian_percent(self, mean=0.5, sigma=0.15):
        while True:
            val = random.gauss(mean, sigma)
            if val >= 0:
                return val


factory.Faker.add_provider(SqdsProvider)


##########################################################################################
##  GAME DATA                                                                           ##
##########################################################################################

class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Category

    api_id = factory.Sequence(lambda n: f"C_APIID_{n}")
    name = factory.Sequence(lambda n: "Category #%s" % n)


class SkillFactory(factory.DjangoModelFactory):
    class Meta:
        model = Skill

    api_id = factory.Sequence(lambda n: f"S_APIID_{n}")
    name = factory.Faker('sentence')
    is_zeta = factory.Sequence(lambda n: n % 4 == 0)


class UnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = Unit

    api_id = factory.Sequence(lambda n: f"U_APIID_{n}")
    name = factory.Faker('name_female')
    skill = factory.RelatedFactoryList(SkillFactory, 'unit',
                                       size=lambda: random.randint(3, 7))

    # noinspection PyUnusedLocal
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of categories were passed in, use them
            for category in extracted:
                self.categories.add(category)


class GearFactory(factory.DjangoModelFactory):
    class Meta:
        model = Gear

    api_id = factory.Sequence(lambda n: f"GR_APIID_{n}")
    name = factory.Faker('name')
    tier = factory.Faker('pyint', min=1, max=12)
    required_rarity = factory.Faker('pyint', min=1, max=12)
    required_level = factory.Faker('pyint', min=1, max=85)

    is_left_hand_g12 = factory.Sequence(lambda n: n % 10 == 0)
    is_right_hand_g12 = factory.Sequence(lambda n: n % 10 == 1)


##########################################################################################
##  PLAYER DATA                                                                         ##
##########################################################################################


class PlayerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Player

    api_id = factory.Sequence(lambda n: f"P_APIID_{n}")
    name = factory.Faker('first_name')
    level = factory.Faker('pyint', min=1, max=85)
    ally_code = factory.Faker('ally_code')
    gp_char = factory.Faker('pyint', min=1, max=3000000)
    gp_ship = factory.Faker('pyint', min=1, max=3000000)
    gp = factory.LazyAttribute(lambda o: o.gp_char + o.gp_ship)


class GuildFactory(factory.DjangoModelFactory):
    class Meta:
        model = Guild

    api_id = factory.Sequence(lambda n: f"G_APIID_{n}")
    name = factory.Faker('name')
    gp = factory.Faker('pyint', min=50000000, max=300000000)


class PlayerUnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlayerUnit

    unit = factory.SubFactory(UnitFactory)

    gp = factory.Faker('pyint', min=1, max=30000)
    rarity = factory.Faker('pyint', min=1, max=7)
    level = factory.Faker('pyint', min=1, max=85)
    gear = factory.Faker('pyint', min=1, max=13)
    equipped_count = factory.Faker('pyint', min=0, max=5)

    speed = factory.Faker('pyint', min=50, max=350)
    health = factory.Faker('pyint', min=1000, max=60000)
    protection = factory.Faker('pyint', min=1000, max=60000)

    physical_damage = factory.Faker('pyint', min=100, max=4000)
    physical_crit_chance = factory.Faker('gaussian_percent')
    special_damage = factory.Faker('pyint', min=100, max=4000)
    special_crit_chance = factory.Faker('gaussian_percent')
    crit_damage = factory.Faker('gaussian_percent', mean=2, sigma=0.3)

    potency = factory.Faker('gaussian_percent')
    tenacity = factory.Faker('gaussian_percent')
    armor = factory.Faker('gaussian_percent')
    resistance = factory.Faker('gaussian_percent')
    armor_penetration = factory.Faker('pyint', min=0, max=200)
    resistance_penetration = factory.Faker('pyint', min=0, max=200)
    health_steal = factory.Faker('gaussian_percent')
    accuracy = factory.Faker('gaussian_percent')

    mod_speed = factory.Faker('pyint', min=0, max=150)
    mod_health = factory.Faker('pyint', min=50, max=1500)
    mod_protection = factory.Faker('pyint', min=100, max=10000)
    mod_physical_damage = factory.Faker('pyint', min=50, max=2000)
    mod_special_damage = factory.Faker('pyint', min=50, max=2000)
    mod_physical_crit_chance = factory.Faker('gaussian_percent')
    mod_special_crit_chance = factory.Faker('gaussian_percent')
    mod_crit_damage = factory.Faker('gaussian_percent')
    mod_potency = factory.Faker('gaussian_percent')
    mod_tenacity = factory.Faker('gaussian_percent')
    mod_armor = factory.Faker('gaussian_percent')
    mod_resistance = factory.Faker('gaussian_percent')
    mod_critical_avoidance = factory.Faker('gaussian_percent')
    mod_accuracy = factory.Faker('gaussian_percent')


class ZetaFactory(factory.DjangoModelFactory):
    class Meta:
        model = Zeta


class PlayerUnitGearFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlayerUnitGear


class ModFactory(factory.DjangoModelFactory):
    class Meta:
        model = Mod

    api_id = factory.Sequence(lambda n: f"M_APIID_{n}")

    mod_set = factory.fuzzy.FuzzyChoice(ModSet.values)

    level = factory.Faker('pyint', min=1, max=15)
    pips = factory.Faker('pyint', min=1, max=6)
    tier = factory.Faker('pyint', min=1, max=5)

    speed = factory.Faker('pyint', min=1, max=25)
    health = factory.Faker('pyint', min=100, max=1000)
    health_percent = factory.Faker('gaussian_percent', mean=.01, sigma=.005)
    protection = factory.Faker('pyint', min=100, max=1000)
    protection_percent = factory.Faker('gaussian_percent', mean=.01, sigma=.005)
    offense = factory.Faker('pyint', min=1, max=250)
    offense_percent = factory.Faker('gaussian_percent', mean=.01, sigma=.005)
    defense = factory.Faker('pyint', min=1, max=30)
    defense_percent = factory.Faker('gaussian_percent', mean=.01, sigma=.005)
    critical_chance = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
    critical_damage = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
    potency = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
    tenacity = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
    critical_avoidance = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
    accuracy = factory.Faker('gaussian_percent', mean=.03, sigma=.01)
