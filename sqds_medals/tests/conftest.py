# noinspection PyUnresolvedReferences
import collections

from sqds_seed.factories import (
    ZetaMedalRuleFactory,
    SkillFactory,
    StatMedalRuleFactory,
    UnitFactory,
)
from sqds.tests.conftest import *


@pytest.fixture()
def medaled_unit(db):
    unit = UnitFactory()
    ZetaMedalRuleFactory(unit=unit, skill=SkillFactory(unit=unit, is_zeta=True))
    StatMedalRuleFactory.create_batch(6, unit=unit)
    return unit


@pytest.fixture()
def over_medaled_unit(db):
    unit = UnitFactory()
    StatMedalRuleFactory.create_batch(8, unit=unit)
    return unit


@pytest.fixture()
def under_medaled_unit(db):
    unit = UnitFactory()
    ZetaMedalRuleFactory(unit=unit, skill=SkillFactory(unit=unit, is_zeta=True))
    StatMedalRuleFactory.create_batch(5, unit=unit)
    return unit
