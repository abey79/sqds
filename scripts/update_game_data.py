from sqds.models import update_game_data, Gear


def run():
    update_game_data()
    Gear.objects.update_or_create_from_swgoh()