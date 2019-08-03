from django.db import models

from sqds.models import Player


class GAPool(models.Model):
    focus_player = models.ForeignKey(Player, on_delete=models.CASCADE,
                                     related_name='ga_pool_set')

    created = models.DateTimeField(auto_now_add=True)


class GAPoolPlayer(models.Model):
    ga_pool = models.ForeignKey(GAPool, on_delete=models.CASCADE,
                                related_name='ga_pool_player_set')
    player = models.ForeignKey(Player, on_delete=models.CASCADE,
                               related_name='ga_pool_player_set')
