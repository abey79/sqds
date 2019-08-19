from sqds.models import Unit, Skill, Category, Gear
from sqds_seed.factories import UnitFactory, CategoryFactory, SkillFactory


def test_units_and_categories(db):
    categories = CategoryFactory.create_batch(4)
    unit1 = UnitFactory(categories=categories[:3])
    unit2 = UnitFactory(categories=[categories[0]])
    unit3 = UnitFactory(categories=[categories[1]])

    assert set(Unit.objects.filter(categories=categories[0])) == {unit1, unit2}
    assert set(Unit.objects.filter(categories=categories[1])) == {unit1, unit3}
    assert set(Unit.objects.filter(categories=categories[2])) == {unit1}
    assert Unit.objects.filter(categories=categories[3]).count() == 0
    assert set(Unit.objects.filter(categories__in=categories[0:2])) == {unit1, unit2,
                                                                        unit3}
    assert set(Category.objects.filter(unit_set=unit1)) == set(categories[:3])


def test_units_and_skills(db):
    unit1 = UnitFactory(skill=[])
    unit2 = UnitFactory(skill=[])
    skill1 = SkillFactory(unit=unit1, is_zeta=True)
    skill2 = SkillFactory(unit=unit1, is_zeta=False)

    assert set(Skill.objects.filter(unit=unit1)) == {skill1, skill2}
    assert set(Skill.objects.filter(unit=unit1, is_zeta=True)) == {skill1}
    assert Skill.objects.filter(unit=unit2).count() == 0


def test_game_data_has_toons(game_data):
    toons = [('BOSSK', 'Bossk'),
             ('DARTHMALAK', 'Darth Malak'),
             ('PADMEAMIDALA', 'Padmé Amidala'),
             ('REY', 'Rey (Scavenger)'),
             ]

    for api_id, toon_name in toons:
        assert Unit.objects.get(api_id=api_id).name == toon_name


def test_game_data_has_zetas(game_data):
    toon_zetas = [('DARTHMALAK', 2),
                  ('DARTHREVAN', 3),
                  ('SITHMARAUDER', 0),
                  ('BOSSK', 2),
                  ('CHIRRUTIMWE', 0),
                  ('BARRISSOFFEE', 1),
                  ]

    for api_id, zeta_count in toon_zetas:
        assert Skill.objects.filter(unit__api_id=api_id,
                                    is_zeta=True).count() == zeta_count


def test_game_data_categories(game_data):
    categories = [('profession_bountyhunter', 'Bounty Hunters'),
                  ('affiliation_imperialtrooper', 'Imperial Trooper'),
                  ('species_tusken', 'Tusken'),
                  ('affiliation_oldrepublic', 'Old Republic')]

    for api_id, name in categories:
        assert Category.objects.get(api_id=api_id).name == name


def test_game_data_unit_categories(game_data):
    tests = [('BOSSK', 'profession_bountyhunter'),
             ('CANDEROUSORDO', 'affiliation_oldrepublic'),
             ('DARTHREVAN', 'affiliation_sithempire')]

    for toon_api_id, cat_api_id in tests:
        assert Unit.objects.get(api_id=toon_api_id) in set(Unit.objects.filter(
            categories__api_id=cat_api_id))


def test_gear_data(game_data, gear_data):
    gears = [('161Salvage', 'Mk 10 Neuro-Saav Electrobinoculars', False, False),
             ('173', 'Mk 9 Kyrotech Battle Computer', False, False),
             ('171', 'Mk 12 ArmaTek Stun Gun', False, True),
             ('165', 'Mk 12 ArmaTek Medpac', True, False),
             ('112', 'Mk 3 Czerka Stun Cuffs', False, False),
             ('G12Finisher_DROIDEKA_A', 'Power Cell Injector (Plasma) - Droideka', False,
              True),
             ]

    for api_id, name, is_left, is_right in gears:
        gear = Gear.objects.get(api_id=api_id)
        assert gear.name == name
        assert gear.is_left_hand_g12 == is_left
        assert gear.is_right_hand_g12 == is_right
