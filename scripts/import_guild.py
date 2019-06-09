from sqds.models import Guild


def run(*args):
    assert len(args)==1
    Guild.objects.update_or_create_from_swgoh(ally_code=int(args[0]))
