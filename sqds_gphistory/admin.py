from django.contrib import admin
from django.db.models.functions import Lower

from sqds.models import Player
from sqds.admin import ReadOnlyMixin
from .models import GP


class PlayerFilter(admin.SimpleListFilter):
    title = 'Player'
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'
    parameter_name = 'player_api_id'

    def lookups(self, request, model_admin):
        return [(i, j) for i, j in (Player
                                    .objects
                                    .values_list('api_id', 'name')
                                    .distinct()
                                    .order_by(Lower('name')))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(player_api_id=self.value())


class UnitFilter(admin.SimpleListFilter):
    title = 'Unit'
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'
    parameter_name = 'unit'

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        return [(i, j) for i, j in (qs
                                    .values_list('unit__id', 'unit__name')
                                    .distinct()
                                    .order_by(Lower('unit__name')))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(unit__id=self.value())


@admin.register(GP)
class GearAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ['gp', 'created']
    list_filter = [PlayerFilter, UnitFilter]
