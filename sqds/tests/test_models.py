from sqds.models import Unit, Category, Skill
from sqds_seed.factories import CategoryFactory, UnitFactory, SkillFactory


def test_units_and_categories(db):
    categories = CategoryFactory.create_batch(4)
    unit1 = UnitFactory(categories=categories[:3])
    unit2 = UnitFactory(categories=[categories[0]])
    unit3 = UnitFactory(categories=[categories[1]])

    assert set(Unit.objects.filter(categories=categories[0])) == {unit1, unit2}
    assert set(Unit.objects.filter(categories=categories[1])) == {unit1, unit3}
    assert set(Unit.objects.filter(categories=categories[2])) == {unit1}
    assert Unit.objects.filter(categories=categories[3]).count() == 0
    assert set(Unit.objects.filter(categories__in=categories[0:2])) == {unit1, unit2,
                                                                        unit3}
    assert set(Category.objects.filter(unit_set=unit1)) == set(categories[:3])


def test_units_and_skills(db):
    unit1 = UnitFactory(skill=[])
    unit2 = UnitFactory(skill=[])
    skill1 = SkillFactory(unit=unit1, is_zeta=True)
    skill2 = SkillFactory(unit=unit1, is_zeta=False)

    assert set(Skill.objects.filter(unit=unit1)) == {skill1, skill2}
    assert set(Skill.objects.filter(unit=unit1, is_zeta=True)) == {skill1}
    assert Skill.objects.filter(unit=unit2).count() == 0

