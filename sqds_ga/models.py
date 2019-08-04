from django.db import models

from sqds.models import Player


class GAPool(models.Model):
    focus_player = models.ForeignKey(Player, on_delete=models.CASCADE,
                                     related_name='ga_pool_set')

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: no cover
        return f"GAPool({self.focus_player.__str__()})"

    class Meta:
        verbose_name = 'GA pool'


class GAPoolPlayer(models.Model):
    ga_pool = models.ForeignKey(GAPool, on_delete=models.CASCADE,
                                related_name='ga_pool_player_set')
    player = models.ForeignKey(Player, on_delete=models.CASCADE,
                               related_name='ga_pool_player_set')

    def __str__(self):  # pragma: no cover
        return (f"GAPoolPlayer({self.player.__str__()} -> "
                f"{self.ga_pool.focus_player.__str__()})")
