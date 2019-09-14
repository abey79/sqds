from django.contrib import admin
from django.utils.html import format_html
from django_admin_listfilter_dropdown.filters import DropdownFilter

from sqds.models import Unit, Skill
from sqds_medals.models import StatMedalRule, ZetaMedalRule, MedaledUnit, Medal


class StatMedalRuleInline(admin.TabularInline):
    model = StatMedalRule
    extra = 0


class ZetaMedalRuleInline(admin.TabularInline):
    model = ZetaMedalRule
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "skill":
            unit = Unit.objects.get(pk=request.resolver_match.kwargs['object_id'])
            kwargs["queryset"] = Skill.objects.filter(unit=unit, is_zeta=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


def unit_rule_count(obj):
    cnt = obj.stat_medal_rule_set.count() + obj.zeta_medal_rule_set.count()

    if cnt == 0:
        s = '<span style="color: #ddd">undefined</span>'
    elif cnt == 7:
        s = '<span style="color:darkgreen"><b>DEFINED</b></span>'
    else:
        s = '<span style="color:red"><b>ERROR: ' + str(cnt) + ' rules</b></span>'

    return format_html(s)


def custom_titled_filter(filter_cls, title):
    class Wrapper(filter_cls):
        def __init__(self, *args, **kwargs):
            instance = super().__init__(*args, **kwargs)
            instance.title = title

    return Wrapper


@admin.register(MedaledUnit)
class MedaledUnitAdmin(admin.ModelAdmin):
    list_display = ['name', unit_rule_count]
    list_filter = (('categories__name', DropdownFilter),)

    fields = ['name']
    readonly_fields = ['name']
    inlines = [
        StatMedalRuleInline,
        ZetaMedalRuleInline
    ]

    ordering = ('name',)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        Medal.objects.update_for_unit(unit=form.instance)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
