from django_extensions.management.jobs import BaseJob

from ..models import GP


class Job(BaseJob):
    help = "Make snapshot of all tracked toons' GP"

    def execute(self):
        GP.objects.create_snapshot('G2737841003')
        GP.objects.create_snapshot('G3397624354')
