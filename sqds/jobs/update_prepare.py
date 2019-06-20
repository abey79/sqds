from django.utils import timezone
from django_extensions.management.jobs import BaseJob

from ..models import Guild


class Job(BaseJob):
    help = "Update PREPARE data from swgoh.help"

    def execute(self):
        should_execute = False
        try:
            guild = Guild.objects.get(api_id='G2737841003')
        except Guild.DoesNotExist:
            should_execute = True

        if not should_execute:
            since_last_update = timezone.now() - guild.last_updated
            if since_last_update.total_seconds() >= 4*3600:
                should_execute = True

        if should_execute:
            Guild.objects.update_or_create_from_swgoh()
