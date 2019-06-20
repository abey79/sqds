from django.db import models

from sqds.models import Unit, Skill


class ScoredUnit(Unit):
    """
    Add score to unit, medal symbol: ⊛
    """

    class Meta:
        proxy = True


class ScoreStatRule(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
                             related_name='score_stat_rule_set')

    stat = models.CharField(max_length=200, choices=[
        ('level', 'Level'),
        ('gear', 'Gear tier'),
        ('rarity', 'Rarity'),
        ('speed', 'Speed'),
        ('health', 'Health'),
        ('protection', 'Protection'),
        ('physical_damage', 'Physical Damage'),
        ('physical_crit_chance', 'Physical CC'),
        ('special_damage', 'Special Damage'),
        ('special_crit_chance', 'Special CC'),
        ('crit_damage', 'Critical Damage'),
        ('potency', 'Potency'),
        ('tenacity', 'Tenacity'),
        ('mod_speed', 'Mod Speed'),
        ('mod_critical_chance', 'Mod CC'),
        ('mod_potency', 'Mod Potency'),
        ('mod_tenacity', 'Mod Tenacity')])
    value = models.FloatField(null=True)

    def __str__(self):
        return "ScoreStatRule: " + self.get_stat_display() + " ≥ " + str(
            self.value)


class ScoreZetaRule(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
                             related_name='score_zeta_rule_set')

    zeta = models.ForeignKey(Skill, on_delete=models.CASCADE)

    def __str__(self):
        return "ScoreZetaRule: " + self.zeta.name
