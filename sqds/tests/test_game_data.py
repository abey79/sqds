import json
import os

import pytest

import swgoh
from sqds.models import update_game_data, Unit, Skill, Category, Gear


def save_game_data():
    """
    Save the game data returned by swgoh.help in game_data.json, for use by the
    game_data() fixture.
    """
    data = {
        'ability_data_list': swgoh.api.get_ability_list(),
        'skill_data_list': swgoh.api.get_skill_list(),
        'unit_data_list': swgoh.api.get_unit_list(),
        'category_data_list': swgoh.api.get_category_list(),
    }

    # noinspection PyUnresolvedReferences
    with open(os.path.join(os.path.dirname(__file__), 'game_data.json'), 'w') as fp:
        json.dump(data, fp)


@pytest.fixture()
def game_data(db):
    with open(os.path.join(os.path.dirname(__file__), 'game_data.json')) as fp:
        data = json.load(fp)
    update_game_data(data['ability_data_list'], data['skill_data_list'],
                     data['unit_data_list'], data['category_data_list'])


def save_gear_data():
    """
    Save the gear data returned by swgoh.help in gear_data.json.
    """
    data = swgoh.api.get_gear_list()

    # noinspection PyUnresolvedReferences
    with open(os.path.join(os.path.dirname(__file__), 'gear_data.json'), 'w') as fp:
        json.dump(data, fp)


@pytest.fixture()
def gear_data(db, mocker):
    with open(os.path.join(os.path.dirname(__file__), 'gear_data.json')) as fp:
        data = json.load(fp)
    mocker.patch('sqds.swgoh.Swgoh.get_gear_list', return_value=data)
    Gear.objects.update_or_create_from_swgoh()


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
