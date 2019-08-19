import json
import os

import pytest

from sqds.models import update_game_data, Gear, Guild


@pytest.fixture()
def game_data(db):
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'game_data.json')) as fp:
        data = json.load(fp)
    update_game_data(data['ability_data_list'], data['skill_data_list'],
                     data['unit_data_list'], data['category_data_list'])


@pytest.fixture()
def gear_data(db, mocker):
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'gear_data.json')) as fp:
        data = json.load(fp)
    mocker.patch('sqds.swgoh.Swgoh.get_gear_list', return_value=data)
    Gear.objects.update_or_create_from_swgoh()


def get_player_data_batch(ally_codes):
    all_players_data = []
    for ally_code in ally_codes:
        # noinspection PyUnresolvedReferences
        with open(os.path.join(os.path.dirname(__file__), 'data',
                               'player_data', f'{ally_code}.json')) as fp:
            data = json.load(fp)
        all_players_data.append(data)
    return all_players_data


@pytest.fixture()
def guild_data(game_data, gear_data, mocker):
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'guild_data.json')) as fp:
        data = json.load(fp)
    mocker.patch('sqds.swgoh.Swgoh.get_guild_list', return_value=data)
    mocker.patch('sqds.swgoh.Swgoh.get_player_data_batch',
                 side_effect=get_player_data_batch)
    Guild.objects.update_or_create_from_swgoh()


@pytest.fixture()
def guild_data_no_player(game_data, gear_data, mocker):
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'guild_data.json')) as fp:
        data = json.load(fp)
    mocker.patch('sqds.swgoh.Swgoh.get_guild_list', return_value=data)
    mocker.patch('sqds.swgoh.Swgoh.get_player_data_batch',
                 side_effect=Exception(
                     'get_player_data_batch should not be called with guild_only=True'))
    Guild.objects.update_or_create_from_swgoh(guild_only=True)
