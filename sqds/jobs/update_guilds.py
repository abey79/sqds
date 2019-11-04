from django.utils import timezone
from django_extensions.management.jobs import BaseJob

from ..models import Player, Guild


def update_guild(ally_code):
    should_execute = False
    try:
        player = Player.objects.get(ally_code=ally_code)
        guild = player.guild;
        since_last_update = timezone.now() - guild.last_updated
        if since_last_update.total_seconds() >= 4 * 3600:
            should_execute = True
    except Player.DoesNotExist:
        should_execute = True

    if should_execute:
        Guild.objects.update_or_create_from_swgoh(ally_code=ally_code)


class Job(BaseJob):
    help = "Update PREPARE and PREPAIRED data from swgoh.help"

    def execute(self):
        update_guild(116235559)
        update_guild(343174317)
