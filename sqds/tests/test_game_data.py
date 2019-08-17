import json
import os

import pytest

import swgoh
from sqds.models import update_game_data, Unit, Skill, Category


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
