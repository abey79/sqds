from django.utils import timezone
from django_extensions.management.jobs import BaseJob

from ..models import update_game_data, Gear


class Job(BaseJob):
    help = "Update game data from swgoh.help"

    def execute(self):
        update_game_data()
        Gear.objects.update_or_create_from_swgoh()
