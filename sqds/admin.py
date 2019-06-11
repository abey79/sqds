from django.contrib import admin
from django.utils.html import format_html
from django.db.models.functions import Lower

from django_admin_listfilter_dropdown.filters import DropdownFilter

from .models import Unit, Player, PlayerUnit, ScoredUnit, \
    ScoreZetaRule, ScoreStatRule, Skill


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    pass


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    pass


def player_unit_summary(obj):
    return format_html("{} <b>{}</b> {}",
                       obj.star_count(),
                       obj.level,
                       obj.colored_gear())


player_unit_summary.short_description = 'Level'


class PlayerFilter(admin.SimpleListFilter):
    title = 'Player'
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'
    parameter_name = 'player'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        return [(i, i) for i in qs.values_list('player__name', flat=True)
            .distinct().order_by(Lower('player__name'))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(player__name__exact=self.value())


class UnitFilter(admin.SimpleListFilter):
    title = 'Unit'
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'
    parameter_name = 'unit'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        return [(i, i) for i in qs.values_list('unit__name', flat=True)
            .distinct().order_by(Lower('unit__name'))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(unit__name__exact=self.value())


@admin.register(PlayerUnit)
class PlayerUnitAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'gp', player_unit_summary,
                    'speed', 'health', 'protection')

    list_filter = (
        PlayerFilter,
        UnitFilter,
        ('rarity', DropdownFilter),
        ('level', DropdownFilter))

    def has_view_permission(self, request, obj=None):
        return False


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

