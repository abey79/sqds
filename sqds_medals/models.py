from django.db import models

from sqds.models import Unit, Skill


class MedaledUnit(Unit):
    """
    Add score to unit, medal symbol: ⊛
    """

    class Meta:
        proxy = True


class StatMedalRule(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
                             related_name='stat_medal_rule_set')

    # noinspection DuplicatedCode
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
        return "StatMedalRule: " + self.get_stat_display() + " ≥ " + str(self.value)


class ZetaMedalRule(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
                             related_name='zeta_medal_rule_set')

    zeta = models.ForeignKey(Skill, on_delete=models.CASCADE)

    def __str__(self):
        return "ZetaMedalRule: " + self.zeta.name


class Medal(models.Model):
    player_unit = models.ForeignKey(Unit, on_delete=models.CASCADE,
                                    related_name='medal_set')

    stat_medal_rule = models.ForeignKey(StatMedalRule, on_delete=models.CASCADE,
                                        null=True, related_name='medal_set')
    zeta_medal_rule = models.ForeignKey(ZetaMedalRule, on_delete=models.CASCADE,
                                        null=True, related_name='medal_set')
