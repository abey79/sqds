from django.test import TestCase
from django.urls import reverse

from sqds_medals.models import StatMedalRule
from sqds_seed.factories import (
    UnitFactory,
    StatMedalRuleFactory,
    SkillFactory,
    ZetaMedalRuleFactory,
)


class MedalViewTest(TestCase):
    def test_no_medals(self):
        url = reverse("sqds_medals:list")
        response = self.client.get(url)
        self.assertContains(response, "Medal list")
        self.assertTemplateUsed(response, "sqds_medals/medal_list.html")

    def test_one_medal(self):
        unit = UnitFactory()
        unit2 = UnitFactory()  # a non-medaled unit
        StatMedalRuleFactory.create_batch(7, unit=unit)

        url = reverse("sqds_medals:list")
        response = self.client.get(url)

        self.assertContains(response, unit.name)
        self.assertNotContains(response, unit2.name)

    # noinspection DuplicatedCode
    def test_wrong_medals(self):
        unit_ok, unit_under, unit_over = UnitFactory.create_batch(3)
        ZetaMedalRuleFactory(
            unit=unit_ok, skill=SkillFactory(unit=unit_ok, is_zeta=True)
        )
        ZetaMedalRuleFactory(
            unit=unit_under, skill=SkillFactory(unit=unit_under, is_zeta=True)
        )
        StatMedalRuleFactory.create_batch(6, unit=unit_ok)
        StatMedalRuleFactory.create_batch(8, unit=unit_over)
        StatMedalRuleFactory.create_batch(5, unit=unit_under)

        url = reverse("sqds_medals:list")
        response = self.client.get(url)

        self.assertContains(response, unit_ok.name)
        self.assertNotContains(response, unit_over.name)
        self.assertNotContains(response, unit_under.name)

    def test_stat_display(self):
        unit = UnitFactory()
        stats = [
            ("speed", 100),
            ("mod_speed", 50),
            ("health", 1000),
            ("protection", 100000),
            ("potency", 0.50),
            ("mod_critical_chance", 0.10),
            ("critical_damage", 2.22),
        ]

        for stat, value in stats:
            StatMedalRuleFactory(unit=unit, stat=stat, value=value)

        url = reverse("sqds_medals:list")
        response = self.client.get(url)

        for stat, value in stats:
            rule = StatMedalRule(stat=stat, value=value)
            self.assertContains(response, str(rule))

    def test_zeta_display(self):
        unit = UnitFactory()
        skill = SkillFactory(unit=unit, is_zeta=True)
        ZetaMedalRuleFactory(unit=unit, skill=skill)
        StatMedalRuleFactory.create_batch(6, unit=unit)

        url = reverse("sqds_medals:list")
        response = self.client.get(url)

        self.assertContains(response, skill.name)
        self.assertContains(response, unit.name)
