from django.db.models.functions import Lower
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

# from django_tables2 import RequestConfig
from django_tables2.views import SingleTableMixin

from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView

from .tables import PlayerTable, PlayerUnitTable
from .models import Category, Guild, Player, PlayerUnit, Unit


def index(request):
    return render(request, 'sqds/index.html', {'guilds': Guild.objects.all()})


def unit(request, player_unit_id):
    player_unit = get_object_or_404(PlayerUnit, pk=player_unit_id)

    return render(request, 'sqds/unit.html', {
        'player_unit': player_unit,
        'square_mod': player_unit.mod_set.filter(slot=0).first(),
        'arrow_mod': player_unit.mod_set.filter(slot=1).first(),
        'diamond_mod': player_unit.mod_set.filter(slot=2).first(),
        'triangle_mod': player_unit.mod_set.filter(slot=3).first(),
        'circle_mod': player_unit.mod_set.filter(slot=4).first(),
        'cross_mod': player_unit.mod_set.filter(slot=5).first()
    })


def player_refresh(request, ally_code):
    Player.objects.update_or_create_from_swgoh(ally_code)
    return redirect('sqds:player', ally_code=ally_code)


# noinspection PyUnusedLocal,PyMethodMayBeStatic
class GPFilter(FilterSet):
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

    # pylint: disable=unused-argument
    def filter_gp(self, queryset, name, value):
        start = int(value) * 500000
        stop = (int(value) + 1) * 500000
        return queryset.filter(gp__gte=start, gp__lt=stop)

    class Meta:
        model = Player
        fields = ['gp']


class GuildView(SingleTableMixin, FilterView):
    table_class = PlayerTable
    model = Player
    template_name = 'sqds/guild.html'
    filterset_class = GPFilter
    table_pagination = {
        'per_page': 50
    }

    def get_queryset(self):
        qs = self.model.objects.filter(
            guild__api_id=self.kwargs['api_id'])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['guild'] = Guild.objects.get(
            api_id=self.kwargs['api_id'])
        context['units_by_api_id'] = Unit.objects.in_bulk(
            field_name='api_id')
        return context


class GuildPlayerUnitsFilter(FilterSet):
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'category']


class GuildUnitsView(SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/players.html'
    filterset_class = GuildPlayerUnitsFilter
    table_pagination = {
        'per_page': 50
    }

    def get_table_kwargs(self):
        return {
            'row_attrs':
            {
                'class': lambda record:
                ('info'
                 if record.player.guild.api_id == self.kwargs['api_id1']
                 else '')
            }}

    def get_queryset(self):
        if 'api_id' in self.kwargs:
            qs = self.model.objects.filter(
                player__guild__api_id=self.kwargs['api_id'])
        elif 'api_id1' in self.kwargs and 'api_id2' in self.kwargs:
            qs = self.model.objects.filter(
                Q(player__guild__api_id=self.kwargs['api_id1'])
                | Q(player__guild__api_id=self.kwargs['api_id2']))
        else:
            qs = self.model.objects.none()

        return qs


class PlayerFilter(GPFilter):
    class Meta(GPFilter.Meta):
        fields = ['guild', 'gp']


class FilteredPlayerListView(SingleTableMixin, FilterView):
    table_class = PlayerTable
    model = Player
    template_name = 'sqds/players.html'
    filterset_class = PlayerFilter
    table_pagination = {
        'per_page': 50
    }


class AllPlayerUnitsFilter(FilterSet):
    player = ChoiceFilter(choices=Player.objects.values_list(
        'id', 'name').order_by(Lower('name')))
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'player', 'category']


class AllPlayerUnitsListView(SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/players.html'
    filterset_class = AllPlayerUnitsFilter
    table_pagination = {
        'per_page': 50
    }

    def get_queryset(self):
        if 'ally_code' in self.kwargs:
            qs = self.model.objects.filter(
                player__ally_code=self.kwargs['ally_code'])
        else:
            qs = self.model.objects.all()

        return qs


class SinglePlayerPlayerUnitsFilter(FilterSet):
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'category']


class SinglePlayerView(SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/single_player.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {
        'per_page': 50
    }

    def get_queryset(self):
        if 'ally_code' in self.kwargs:
            if not Player.objects.filter(ally_code=self.kwargs['ally_code']):
                Player.objects.update_or_create_from_swgoh(
                    self.kwargs['ally_code'])

            qs = self.model.objects.filter(
                player__ally_code=self.kwargs['ally_code'])
        else:
            qs = self.model.objects.none()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player'] = Player.objects.get(
            ally_code=self.kwargs['ally_code'])
        return context


class PlayerCompareView(SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/player_compare.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {
        'per_page': 50
    }

    def get_table_kwargs(self):
        return {
            'row_attrs':
            {
                'class': lambda record:
                ('info'
                 if record.player.ally_code == self.kwargs['ally_code1']
                 else '')
            }}

    def get_queryset(self):
        if 'ally_code1' in self.kwargs and 'ally_code2' in self.kwargs:
            if not Player.objects.filter(ally_code=self.kwargs['ally_code1']):
                Player.objects.update_or_create_from_swgoh(
                    self.kwargs['ally_code1'])

            if not Player.objects.filter(ally_code=self.kwargs['ally_code2']):
                Player.objects.update_or_create_from_swgoh(
                    self.kwargs['ally_code2'])

            qs = self.model.objects.filter(
                Q(player__ally_code=self.kwargs['ally_code1'])
                | Q(player__ally_code=self.kwargs['ally_code2']))
        else:
            qs = self.model.objects.none()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player1'] = Player.objects.get(
            ally_code=self.kwargs['ally_code1'])
        context['player2'] = Player.objects.get(
            ally_code=self.kwargs['ally_code2'])
        return context
