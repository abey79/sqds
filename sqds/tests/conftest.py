import json
import numbers
import os

import pytest

from sqds.models import update_game_data, Gear, Guild


def data_path(path, *more_path):
    return os.path.join(os.path.dirname(__file__), path, *more_path)


def load_data(path, *more_path):
    with open(data_path(path, *more_path)) as fp:
        data = json.load(fp)
    return data


@pytest.fixture()
def patched_swgoh(mocker):
    def get_guild_list(ally_code):
        """
        Return guild data based on an ally code. This is pretty badly hardcoded based
        on the fact that we have 1 guild data file, in which all available player
        files belong.
        """
        player_files = os.listdir(data_path('data', 'player_data'))
        ally_code_available = [int(s[:-5]) for s in player_files if s.endswith('.json')]
        if ally_code in ally_code_available + [116235559]:
            return load_data('data', 'guild_data.json')
        else:
            raise NotImplemented('Guild data does not exist')

    def get_player_data_batch(ally_codes):
        if isinstance(ally_codes, numbers.Integral):
            ally_codes = [ally_codes]
        player_data = []
        for ally_code in ally_codes:
            player_data.append(load_data('data', 'player_data', str(ally_code) + '.json'))
        return player_data

    data = load_data('data', 'game_data.json')
    swgoh_patches = {
        'get_gear_list': mocker.patch('sqds.swgoh.Swgoh.get_gear_list',
                                      return_value=load_data('data', 'gear_data.json')),
        'get_ability_list': mocker.patch('sqds.swgoh.Swgoh.get_ability_list',
                                         return_value=data['ability_data_list']),
        'get_skill_list': mocker.patch('sqds.swgoh.Swgoh.get_skill_list',
                                       return_value=data['skill_data_list']),
        'get_unit_list': mocker.patch('sqds.swgoh.Swgoh.get_unit_list',
                                      return_value=data['unit_data_list']),
        'get_category_list': mocker.patch('sqds.swgoh.Swgoh.get_category_list',
                                          return_value=data['category_data_list']),
        'get_guild_list': mocker.patch('sqds.swgoh.Swgoh.get_guild_list',
                                       side_effect=get_guild_list),
        'get_player_data_batch': mocker.patch('sqds.swgoh.Swgoh.get_player_data_batch',
                                              side_effect=get_player_data_batch)
    }

    return swgoh_patches


@pytest.fixture()
def game_data(db, patched_swgoh):
    update_game_data()
    Gear.objects.update_or_create_from_swgoh()


@pytest.fixture()
def guild_data(game_data, patched_swgoh):
    Guild.objects.update_or_create_from_swgoh()


@pytest.fixture()
def guild_data_no_player(game_data, patched_swgoh):
    Guild.objects.update_or_create_from_swgoh(guild_only=True)
