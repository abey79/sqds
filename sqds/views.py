import collections
from textwrap import wrap

import numpy as np
import plotly.graph_objs as go
import plotly.offline as opy
from django.contrib import messages
from django.db.models import Q, F
from django.db.models.functions import Lower
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from django.views.generic import DetailView, TemplateView
from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from meta.views import MetadataMixin

from sqds_ga.models import GAPool
from .models import Category, Guild, Player, PlayerUnit, Unit
from .tables import PlayerTable, PlayerUnitTable
from .utils import format_large_int


def index(request):
    return render(request, 'sqds/index.html', {'guilds': Guild.objects.all()})


class UnitView(MetadataMixin, DetailView):
    model = PlayerUnit
    context_object_name = 'player_unit'
    template_name = 'sqds/unit.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate_stats()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        try:
            obj = queryset.get(player__ally_code=self.kwargs['ally_code'],
                               unit__api_id=self.kwargs['unit_api_id'])
        except (KeyError, queryset.model.DoesNotExist):
            raise Http404("No unit found found matching the query")
        return obj

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
                      .annotate_faction_gp()
                      .get(api_id=self.kwargs['api_id']))

    def get_queryset(self):
        qs = (self.model.objects
              .filter(guild__api_id=self.kwargs['api_id'])
              .annotate_stats()
              .annotate_faction_gp()
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
        return (self.model.objects
                .filter(player__guild__api_id=self.kwargs['api_id'])
                .annotate_stats()
                .select_related('unit', 'player'))

    def get_meta_title(self, **kwargs):
        return "Guild units: " + self.guild.name

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        return "{} characters, ordered by {}".format(
            context['table'].paginator.count,
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
        return (self.model.objects
                .filter(Q(player__guild__api_id=self.kwargs['api_id1'])
                        | Q(player__guild__api_id=self.kwargs['api_id2']))
                .annotate_stats()
                .select_related('unit', 'player'))

    def get_meta_title(self, **kwargs):
        return format_html("Guild comparison units: <b>{}</b> vs. {}",
                           self.guild1.name, self.guild2.name)

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        return "{} characters, ordered by {}".format(
            context['table'].paginator.count,
            sort_string.replace('-', 'descending ').replace('_', ' '))


class SinglePlayerPlayerUnitsFilter(FilterSet):
    category = ChoiceFilter(field_name='unit__categories',
                            choices=Category.objects.values_list(
                                'id', 'name').order_by(Lower('name')))

    class Meta:
        model = PlayerUnit
        fields = ['unit', 'category']


def player_register_me(request, ally_code):
    player = get_object_or_404(Player, ally_code=ally_code)
    max_age = 365 * 24 * 60 * 60
    response = redirect('sqds:player', ally_code=ally_code)
    response.set_cookie('sqds_my_name', player.name, max_age=max_age)
    response.set_cookie('sqds_my_ally_code', player.ally_code, max_age=max_age)
    response.set_cookie('sqds_my_guild_name', player.guild.name, max_age=max_age)
    response.set_cookie('sqds_my_guild_api_id', player.guild.api_id, max_age=max_age)
    messages.info(request, f'Successfully registered as {player.name}.')
    return response


def player_unregister_me(request):
    if 'sqds_my_ally_code' in request.COOKIES:
        response = redirect('sqds:player', ally_code=request.COOKIES['sqds_my_ally_code'])
    else:
        response = redirect('sqds:index')
    response.delete_cookie('sqds_my_name')
    response.delete_cookie('sqds_my_ally_code')
    response.delete_cookie('sqds_my_guild_name')
    response.delete_cookie('sqds_my_guild_api_id')
    messages.info(request, 'Successfully unregistered.')
    return response


def player_refresh(request, ally_code):
    Player.objects.update_or_create_from_swgoh(ally_code)
    return redirect('sqds:player', ally_code=ally_code)


class SinglePlayerView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/single_player.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        ally_code = self.kwargs['ally_code']
        if not Player.objects.filter(ally_code=ally_code):
            Player.objects.update_or_create_from_swgoh(ally_code)

        try:
            self.player = (Player.objects
                           .annotate_stats()
                           .get(ally_code=ally_code))
        except Player.DoesNotExist:
            raise Http404(f'Player {ally_code} could not be loaded')

    def get_queryset(self):
        return (self.model.objects
                .filter(player__ally_code=self.kwargs['ally_code'])
                .annotate_stats()
                .select_related('unit', 'player'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player'] = self.player
        context['ga_pools'] = (GAPool.objects
                               .filter(focus_player=self.player)
                               .order_by('-created')[:10])
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


##########################################################################################
## PLAYER COMPARE VIEW                                                                  ##
##########################################################################################

PLAYER_COMPARE_KEY_TOONS = (
    'DARTHREVAN',
    'BASTILASHANDARK',
    'DARTHMALAK',
    'SITHMARAUDER',
    'JEDIKNIGHTREVAN',
    'GRANDADMIRALTHRAWN',
    'COMMANDERLUKESKYWALKER',
    'DARTHTRAYA',
    'GRANDMASTERYODA',
    'KYLORENUNMASKED',
    'BOSSK',
    'ENFYSNEST',
    'GRIEVOUS',
    'GEONOSIANBROODALPHA',
    'SHAAKTI',
    'DAKA',
    'NIGHTSISTERZOMBIE',
)


class PlayerCompareView(MetadataMixin, TemplateView):
    template_name = 'sqds/player_compare.html'

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        Player.objects.ensure_exist([self.kwargs['ally_code1'],
                                     self.kwargs['ally_code2']])

        qs = (Player.objects
              .filter(ally_code__in=[self.kwargs['ally_code1'],
                                     self.kwargs['ally_code2']])
              .annotate_stats()
              .select_related('guild'))

        for p in qs:
            if p.ally_code == self.kwargs['ally_code1']:
                self.player1 = p
            if p.ally_code == self.kwargs['ally_code2']:
                self.player2 = p

        p1_units = PlayerUnit.objects.dict_from_ally_code(
            self.kwargs['ally_code1'], PLAYER_COMPARE_KEY_TOONS)
        p2_units = PlayerUnit.objects.dict_from_ally_code(
            self.kwargs['ally_code2'], PLAYER_COMPARE_KEY_TOONS)

        id_to_name = {v['api_id']: v['name'] for v in
                      Unit.objects.values('api_id', 'name')}

        self.units = collections.OrderedDict()
        for toon in PLAYER_COMPARE_KEY_TOONS:
            self.units[id_to_name[toon]] = dict(
                player1=p1_units[toon] if toon in p1_units else None,
                player2=p2_units[toon] if toon in p2_units else None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player1'] = self.player1
        context['player2'] = self.player2
        context['units'] = self.units
        context['players'] = [self.player1, self.player2]
        context['mod_speed_graph'] = self.generate_mod_speed_graph()
        context['gp_analysis_graph'] = self.generate_gp_analysis_graph()
        return context

    def get_meta_title(self, **kwargs):
        return "Player compare"

    def get_meta_description(self, context=None):
        format_string = "Comparision between {}'s {} (ally code: {}) " \
                        "and {}'s {} (ally code: {})"
        return format_string.format(
            self.player1.guild.name,
            self.player1.name,
            '-'.join(wrap(str(self.player1.ally_code), 3)),
            self.player2.guild.name,
            self.player2.name,
            '-'.join(wrap(str(self.player2.ally_code), 3)))

    def generate_mod_speed_graph(self):
        traces = []
        for player in [self.player1, self.player2]:
            qs = (PlayerUnit.objects
                  .filter(player__name=player)
                  .order_by('-mod_speed')
                  .values_list('mod_speed', 'unit__name'))
            values = list(zip(*qs))
            y_data = values[0]
            labels = values[1]
            traces.append(go.Scatter(
                x=list(range(len(y_data))),
                y=y_data,
                text=labels,
                name=player.name,
                line=dict(shape='hv')))

        layout = go.Layout(xaxis={'title': 'Characters, sorted by decreasing mod speed'},
                           yaxis={'title': 'mod speed bonus'},
                           showlegend=False,
                           height=400,
                           margin=go.layout.Margin(l=60, r=10, b=60, t=40, pad=4))
        figure = go.Figure(data=traces, layout=layout)
        return opy.plot(figure, auto_open=False, output_type='div')

    def generate_gp_analysis_graph(self):
        gp1, gp2 = [np.cumsum(np.array(PlayerUnit.objects
                                       .filter(player__name=player)
                                       .order_by('-gp')
                                       .values_list('gp', flat=True)))
                    for player in [self.player1, self.player2]]

        max_len = min(len(gp1), len(gp2), 100)
        gp1 = gp1[:max_len]
        gp2 = gp2[:max_len]
        mean_gp = (gp1 + gp2) * 0.5

        traces = [go.Scatter(y=gp - mean_gp, name=player.name) for gp, player in
                  [(gp1, self.player1), (gp2, self.player2)]]

        layout = go.Layout(xaxis={'title': 'Characters, sorted by decreasing GP'},
                           yaxis={'title': 'Dev. from mean cumul. GP'},
                           showlegend=False,
                           height=400,
                           margin=go.layout.Margin(l=60, r=10, b=60, t=40, pad=4))
        figure = go.Figure(data=traces, layout=layout)
        return opy.plot(figure, auto_open=False, output_type='div')


class PlayerCompareUnitsView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = PlayerUnitTable
    model = PlayerUnit
    template_name = 'sqds/player_compare_units.html'
    filterset_class = SinglePlayerPlayerUnitsFilter
    table_pagination = {'per_page': 50}

    # noinspection PyAttributeOutsideInit
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        Player.objects.ensure_exist([self.kwargs['ally_code1'],
                                     self.kwargs['ally_code2']])

        self.player1 = get_object_or_404(Player, ally_code=self.kwargs['ally_code1'])
        self.player2 = get_object_or_404(Player, ally_code=self.kwargs['ally_code2'])

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
        return (self.model.objects
                .filter(Q(player__ally_code=self.kwargs['ally_code1'])
                        | Q(player__ally_code=self.kwargs['ally_code2']))
                .annotate_stats()
                .select_related('unit', 'player'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['player1'] = self.player1
        context['player2'] = self.player2
        return context

    def get_meta_title(self, **kwargs):
        return "Player unit comparison: {} vs. {}".format(self.player1.name,
                                                          self.player2.name)

    def get_meta_description(self, context=None):
        sort_string = str(context['table'].order_by)
        format_string = "{} characters, ordered by {}, from {} (ally code: {}) " \
                        "and {} (ally code: {})"
        return format_string.format(
            0,  # context['object_list'].count(),
            sort_string.replace('-', 'descending ').replace('_', ' '),
            self.player1.name,
            '-'.join(wrap(str(self.player1.ally_code), 3)),
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
        return self.model.objects.annotate_stats().annotate_faction_gp()


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
            qs = (self.model.objects
                  .filter(player__ally_code=self.kwargs['ally_code'])
                  .annotate_stats()
                  .select_related('unit', 'player'))
        else:
            qs = self.model.objects.all().annotate_stats().select_related('unit',
                                                                          'player')

        return qs
