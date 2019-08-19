import json
import os

import swgoh


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
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'game_data.json'), 'w') as fp:
        json.dump(data, fp)


def save_gear_data():
    """
    Save the gear data returned by swgoh.help in gear_data.json.
    """
    data = swgoh.api.get_gear_list()

    # noinspection PyUnresolvedReferences
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'gear_data.json'), 'w') as fp:
        json.dump(data, fp)


def save_guild_data():
    """
    Save some guild data returned by swgoh.help to json files to be used for swgoh
    mocking. For efficiency purpose, we keep data for only 5 players.
    """
    guild_data = swgoh.api.get_guild_list(116235559)
    del guild_data['roster'][5:]

    # noinspection PyUnresolvedReferences
    with open(os.path.join(os.path.dirname(__file__),
                           'data', 'guild_data.json'), 'w') as fp:
        json.dump(guild_data, fp)

    ally_codes = [p['allyCode'] for p in guild_data['roster']]
    all_player_data = swgoh.api.get_player_data_batch(ally_codes)

    for player_data in all_player_data:
        ally_code = player_data['allyCode']
        # noinspection PyUnresolvedReferences
        with open(os.path.join(os.path.dirname(__file__), 'data',
                               'player_data', f'{ally_code}.json'), 'w') as fp:
            json.dump(player_data, fp)
