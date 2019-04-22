from django.db.models.functions import Lower

# from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin

from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView

from .tables import PlayerTable, PlayerUnitTable
from .models import Player, PlayerUnit


class PlayerFilter(FilterSet):
    gp = ChoiceFilter(choices=(
        (0, '<500k'),
        (1, '500k-1M'),
        (2, '1M-1.5M'),
        (3, '1.5M-2M'),
        (4, '2M-2.5M'),
        (5, '2.5M-3M'),
        (6, '3M-3.5M'),
        (7, '3.5M-4M'),
        (8, '4M-4.5M'),
        (9, '4.5M-5M'),
        (10, '5M-5.5M'),
        (11, '5.5M-6M'),
    ), method='filter_gp')

    def filter_gp(self, queryset, name, value):
        start = int(value) * 500000
        stop = (int(value) + 1) * 500000
        return queryset.filter(gp__gte=start, gp__lt=stop)

    class Meta:
        model = Player
        fields = ['guild', 'gp']


class FilteredPlayerListView(SingleTableMixin, FilterView):
    table_class = PlayerTable
    model = Player
    template_name = 'sqds/players.html'
    filterset_class = PlayerFilter


class PlayerUnitFilter(FilterSet):
    player = ChoiceFilter(choices=Player.objects.values_list(
        'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'player']


class FilteredPlayerUnitListView(SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/players.html'
    filterset_class = PlayerUnitFilter
