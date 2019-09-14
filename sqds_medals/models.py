from django.db import models, transaction
from django.db.models import Count

from sqds.models import Unit, Skill, PlayerUnit, Zeta, Player


class MedaledUnit(Unit):
    """
    Add score to unit, medal symbol: ⊛
    """

    class Meta:
        proxy = True


class StatMedalRule(models.Model):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="stat_medal_rule_set"
    )

    # noinspection DuplicatedCode
    stat = models.CharField(
        max_length=200,
        choices=[
            ("level", "Level"),
            ("gear", "Gear tier"),
            ("rarity", "Rarity"),
            ("speed", "Speed"),
            ("health", "Health"),
            ("protection", "Protection"),
            ("physical_damage", "Physical Damage"),
            ("physical_crit_chance", "Physical CC"),
            ("special_damage", "Special Damage"),
            ("special_crit_chance", "Special CC"),
            ("crit_damage", "Critical Damage"),
            ("potency", "Potency"),
            ("tenacity", "Tenacity"),
            ("mod_speed", "Mod Speed"),
            ("mod_critical_chance", "Mod CC"),
            ("mod_potency", "Mod Potency"),
            ("mod_tenacity", "Mod Tenacity"),
        ],
    )
    value = models.FloatField(null=True)

    def __str__(self):
        return self.get_stat_display() + " ≥ " + str(self.value)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(unit={self.unit}, stat={self.stat}, "
            f"value={self.value})"
        )


class ZetaMedalRule(models.Model):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="zeta_medal_rule_set"
    )

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    def __str__(self):
        return f"Zeta: {self.skill.name}"

    def __repr__(self):
        return f"{self.__class__.__name__}(unit={self.unit}, skill={self.skill})"


class MedalManager(models.Manager):
    def update_for_unit(self, unit):
        """
        Update medals for all player units of `unit` type.
        :param unit: unit to update
        :return:
        """

        with transaction.atomic():
            self.model.objects.filter(player_unit__unit=unit).delete()

            if unit.stat_medal_rule_set.count() + unit.zeta_medal_rule_set.count() != 7:
                return

            stat_rules = StatMedalRule.objects.filter(unit=unit)
            zeta_rules = ZetaMedalRule.objects.filter(unit=unit)

            medals = []
            for rule in stat_rules:
                filter_args = {rule.stat + "__gte": rule.value, "unit": rule.unit}

                medals.extend(
                    self.model(player_unit=pu, stat_medal_rule=rule)
                    for pu in PlayerUnit.objects.filter(**filter_args)
                )

            for rule in zeta_rules:
                medals.extend(
                    self.model(player_unit=z.player_unit, zeta_medal_rule=rule)
                    for z in Zeta.objects.filter(
                        skill=rule.skill, player_unit__unit=rule.unit
                    )
                )

            self.model.objects.bulk_create(medals)

    def update_all(self, ally_codes=None):
        """
        Update medals for all toons. If ally codes are provided, update medals only for
        these ally codes.
        :param ally_codes: iterable of ally code, or None to update all medals
        """
        subquery = Unit.objects.annotate(
            tot=Count("stat_medal_rule_set", distinct=True)
            + Count("zeta_medal_rule_set", distinct=True)
        ).filter(tot=7)

        stat_rules = StatMedalRule.objects.filter(unit__in=subquery)
        zeta_rules = ZetaMedalRule.objects.filter(unit__in=subquery)

        medal_args = {}
        pu_args = {}
        if ally_codes:
            medal_args["player_unit__player__in"] = list(
                Player.objects.filter(ally_code__in=list(ally_codes))
            )
            pu_args["player__in"] = list(
                Player.objects.filter(ally_code__in=list(ally_codes))
            )

        with transaction.atomic():
            # Delete all medals assigned to player unit for which rules are no longer
            # properly set
            self.model.objects.exclude(player_unit__unit__in=subquery).delete()  # WRONG
            self.model.objects.filter(**medal_args).delete()

            medals = []
            for rule in stat_rules:
                filter_args = {rule.stat + "__gte": rule.value, "unit": rule.unit}

                medals.extend(
                    self.model(player_unit=pu, stat_medal_rule=rule)
                    for pu in PlayerUnit.objects.filter(**filter_args, **pu_args)
                )

            for rule in zeta_rules:
                medals.extend(
                    self.model(player_unit=z.player_unit, zeta_medal_rule=rule)
                    for z in Zeta.objects.filter(
                        skill=rule.skill, player_unit__unit=rule.unit, **medal_args
                    )
                )

            self.model.objects.bulk_create(medals)


class Medal(models.Model):
    player_unit = models.ForeignKey(
        PlayerUnit, on_delete=models.CASCADE, related_name="medal_set"
    )

    stat_medal_rule = models.ForeignKey(
        StatMedalRule, on_delete=models.CASCADE, null=True, related_name="medal_set"
    )
    zeta_medal_rule = models.ForeignKey(
        ZetaMedalRule, on_delete=models.CASCADE, null=True, related_name="medal_set"
    )

    objects = MedalManager()
