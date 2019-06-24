from textwrap import wrap

from django.db.models.functions import Lower
from django.db.models import Q, F
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.views.generic import DetailView

from django_tables2.views import SingleTableMixin
from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView
from meta.views import MetadataMixin

from .utils import format_large_int
from .tables import PlayerTable, PlayerUnitTable
from .models import Category, Guild, Player, PlayerUnit, Unit


def index(request):
    return render(request, 'sqds/index.html', {'guilds': Guild.objects.all()})


class UnitView(MetadataMixin, DetailView):
    model = PlayerUnit
    context_object_name = 'player_unit'
    template_name = 'sqds/unit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        player_unit = context['player_unit']
        context['square_mod'] = player_unit.mod_set.filter(slot=0).first()
        context['arrow_mod'] = player_unit.mod_set.filter(slot=1).first()
        context['diamond_mod'] = player_unit.mod_set.filter(slot=2).first()
        context['triangle_mod'] = player_unit.mod_set.filter(slot=3).first()
        context['circle_mod'] = player_unit.mod_set.filter(slot=4).first()
        context['cross_mod'] = player_unit.mod_set.filter(slot=5).first()
        return context

    def get_meta_title(self, context=None):
        player_unit = context['player_unit']
        return "{}'s {}".format(
            player_unit.player.name,
            player_unit.unit.name)

    def get_meta_description(self, context=None):
        player_unit = context['player_unit']
        return "Gear {}, level {}, {}★, {} GP".format(
            player_unit.gear,
            player_unit.level,
            player_unit.rarity,
            format_large_int(player_unit.gp))


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

    def filter_gp(self, queryset, name, value):
        start = int(value) * 500000
        stop = (int(value) + 1) * 500000
        return queryset.filter(gp__gte=start, gp__lt=stop)

    class Meta:
        model = Player
        fields = ['gp']


class GuildView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = PlayerTable
    model = Player
    template_name = 'sqds/guild.html'
    filterset_class = GPFilter
    table_pagination = False

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # noinspection PyAttributeOutsideInit
        self.guild = (Guild.objects
                      .annotate_stats()
                      .annotate_separatist_gp()
                      .get(api_id=self.kwargs['api_id']))

    def get_queryset(self):
        qs = (self.model.objects
              .filter(guild__api_id=self.kwargs['api_id'])
              .annotate_stats()
              .annotate_separatist_gp()
              .annotate(guild_name=F('guild__name'), guild_api_id=F('guild__api_id')))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['guild'] = self.guild
        context['units_by_api_id'] = Unit.objects.in_bulk(
            field_name='api_id')
        return context

    def get_meta_title(self, **kwargs):
        return "Guild: " + self.guild.name

    def get_meta_description(self, **kwargs):
        return "{} players, {} GP".format(
            self.guild.player_count,
            format_large_int(self.guild.gp))


class GuildPlayerUnitsFilter(FilterSet):
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'category']


class GuildUnitsView(MetadataMixin, SingleTableMixin, FilterView):
    """
    Render the unit list for a given guild.
    """
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/guild_units.html'
    filterset_class = GuildPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.guild = Guild.objects.get(api_id=self.kwargs['api_id'])

    def get_queryset(self):
        qs = self.model.objects.filter(player__guild__api_id=self.kwargs['api_id'])
        return qs

    def get_meta_title(self, **kwargs):
        return "Guild units: " + self.guild.name

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        return "{} characters, ordered by {}".format(
            context['object_list'].count(),
            sort_string.replace('-', 'descending ').replace('_', ' '))


class GuildComparisonUnitsView(MetadataMixin, SingleTableMixin, FilterView):
    """
    Render the unit list of two guilds, with one set of unit highlighted.
    """
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/guild_units.html'
    filterset_class = GuildPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.guild1 = Guild.objects.get(api_id=self.kwargs['api_id1'])
        self.guild2 = Guild.objects.get(api_id=self.kwargs['api_id2'])

    def get_table_kwargs(self):
        return {
            'row_attrs':
                {
                    'class': lambda record:
                    ('info'
                     if record.player.guild.api_id == self.kwargs[
                        'api_id1']
                     else '')
                }}

    def get_queryset(self):
        qs = self.model.objects.filter(
            Q(player__guild__api_id=self.kwargs['api_id1'])
            | Q(player__guild__api_id=self.kwargs['api_id2']))

        return qs

    def get_meta_title(self, **kwargs):
        return format_html("Guild comparison units: <b>{}</b> vs. {}",
                           self.guild1.name, self.guild2.name)

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        return "{} characters, ordered by {}".format(
            context['object_list'].count(),
            sort_string.replace('-', 'descending ').replace('_', ' '))


class SinglePlayerPlayerUnitsFilter(FilterSet):
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'category']


class SinglePlayerView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/single_player.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if not Player.objects.filter(ally_code=self.kwargs['ally_code']):
            Player.objects.update_or_create_from_swgoh(self.kwargs['ally_code'])
        self.player = (Player.objects
                       .annotate_stats()
                       .get(ally_code=self.kwargs['ally_code']))

    def get_queryset(self):
        return self.model.objects.filter(player__ally_code=self.kwargs['ally_code'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player'] = self.player
        return context

    def get_meta_title(self, **kwargs):
        return "Player: {}".format(self.player.name)

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        format_string = "{} characters, ordered by {}, from {}'s {} (ally code: {})"
        return format_string.format(
            context['object_list'].count(),
            sort_string.replace('-', 'descending ').replace('_', ' '),
            self.player.guild.name,
            self.player.name,
            '-'.join(wrap(str(self.player.ally_code), 3)))


class PlayerCompareView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/player_compare.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if not Player.objects.filter(ally_code=self.kwargs['ally_code1']):
            Player.objects.update_or_create_from_swgoh(self.kwargs['ally_code1'])
        if not Player.objects.filter(ally_code=self.kwargs['ally_code2']):
            Player.objects.update_or_create_from_swgoh(
                self.kwargs['ally_code2'])
        self.player1 = (Player.objects
                        .annotate_stats()
                        .get(ally_code=self.kwargs['ally_code1']))
        self.player2 = (Player.objects
                        .annotate_stats()
                        .get(ally_code=self.kwargs['ally_code2']))

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
        return self.model.objects.filter(
            Q(player__ally_code=self.kwargs['ally_code1'])
            | Q(player__ally_code=self.kwargs['ally_code2']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player1'] = self.player1
        context['player2'] = self.player2
        return context

    def get_meta_title(self, **kwargs):
        return "Player compare: {} vs. {}".format(self.player1.name, self.player2.name)

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        format_string = "{} characters, ordered by {}, from {}'s {} (ally code: {}) " \
                        "and {}'s {} (ally code: {})"
        return format_string.format(
            context['object_list'].count(),
            sort_string.replace('-', 'descending ').replace('_', ' '),
            self.player1.guild.name,
            self.player1.name,
            '-'.join(wrap(str(self.player1.ally_code), 3)),
            self.player2.guild.name,
            self.player2.name,
            '-'.join(wrap(str(self.player2.ally_code), 3)))


#######################################################################
## LEGACY VIEW                                                       ##
## These views should likely be removed as they have limited purpose ##
#######################################################################

class PlayerFilter(GPFilter):
    class Meta(GPFilter.Meta):
        fields = ['guild', 'gp']


class FilteredPlayerListView(SingleTableMixin, FilterView):
    table_class = PlayerTable
    model = Player
    template_name = 'sqds/player_list.html'
    filterset_class = PlayerFilter
    table_pagination = {'per_page': 50}

    def get_queryset(self):
        return self.model.objects.annotate_stats().annotate_separatist_gp()


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
    template_name = 'sqds/unit_list.html'
    filterset_class = AllPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    def get_queryset(self):
        if 'ally_code' in self.kwargs:
            qs = self.model.objects.filter(
                player__ally_code=self.kwargs['ally_code'])
        else:
            qs = self.model.objects.all()

        return qs
