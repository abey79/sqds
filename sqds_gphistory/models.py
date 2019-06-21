from django.db import models

from sqds.models import PlayerUnit, Unit


class GPManager(models.Manager):
    @staticmethod
    def create_snapshot(guild_api_id):
        qs = PlayerUnit.objects.filter(player__guild__api_id=guild_api_id).values(
            'unit',
            'player__api_id',
            'gp')

        objs = (GP(unit=Unit(pu['unit']), player_api_id=pu['player__api_id'], gp=pu['gp'])
                for
                pu in qs)
        GP.objects.bulk_create(objs)


class GP(models.Model):
    unit = models.ForeignKey('sqds.Unit', on_delete=models.CASCADE)
    player_api_id = models.CharField(max_length=50, db_index=True)
    gp = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)

    objects = GPManager()

    def __str__(self):
        return "GP(" + str(self.unit.id) + ", '" + self.player_api_id + "', " \
               + str(self.gp) + ")"

    class Meta:
        verbose_name = "GP"
        ordering = ['created']
