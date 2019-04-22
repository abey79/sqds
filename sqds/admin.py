from django.contrib import admin
from django.utils.html import format_html
from django.db.models.functions import Lower

from django_admin_listfilter_dropdown.filters import DropdownFilter

from .models import Unit, Player, PlayerUnit


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
