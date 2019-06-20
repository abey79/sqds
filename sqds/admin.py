from django.contrib import admin
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter

from .models import Unit, ScoredUnit, ScoreZetaRule, ScoreStatRule, Skill, Gear


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class ReadOnlyMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SkillInline(ReadOnlyMixin, admin.TabularInline):
    model = Skill
    extra = 0


@admin.register(Unit)
class UnitAdmin(ReadOnlyMixin, admin.ModelAdmin):
    inlines = [SkillInline]


@admin.register(Gear)
class GearAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass


@admin.register(Skill)
class SkillAdmin(ReadOnlyMixin, admin.ModelAdmin):
    pass


class ScoreStatRuleInline(admin.TabularInline):
    model = ScoreStatRule
    extra = 0


class ScoreZetaRuleInline(admin.TabularInline):
    model = ScoreZetaRule
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "zeta":
            unit = Unit.objects.get(pk=request.resolver_match.kwargs['object_id'])
            kwargs["queryset"] = Skill.objects.filter(unit=unit, is_zeta=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


def unit_rule_count(obj):
    cnt = obj.score_stat_rule_set.count() + obj.score_zeta_rule_set.count()

    if cnt == 0:
        s = '<span style="color: #ddd">undefined</span>'
    elif cnt == 7:
        s = '<span style="color:darkgreen"><b>DEFINED</b></span>'
    else:
        s = '<span style="color:red"><b>ERROR: ' + str(cnt) + ' rules</b></span>'

    return format_html(s)


@admin.register(ScoredUnit)
class ScoredUnitAdmin(admin.ModelAdmin):
    list_display = ['name', unit_rule_count]
    list_filter = [
        ('categories__name', DropdownFilter)]

    fields = ['name']
    readonly_fields = ['name']
    inlines = [
        ScoreStatRuleInline,
        ScoreZetaRuleInline
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
