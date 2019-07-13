import pandas as pd
import plotly.graph_objs as go
import plotly.offline as opy
from django.db.models import Sum, Q, Case, When, BooleanField, OuterRef, Subquery
from django.db.models.functions import TruncDay
from django.views.generic import TemplateView
from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from meta.views import MetadataMixin

from sqds.models import Player, Unit, PlayerUnit, Guild
from sqds_gphistory.models import GP
from .tables import GeoTBPlayerTable


##########################################################################################
## GEO TB PLAYER VIEW                                                                   ##
##########################################################################################


class DRMalakFilterSet(FilterSet):
    has_dr = ChoiceFilter(field_name='has_dr',
                          choices=((True, 'Revan'), (False, 'No Revan')))
    has_malak = ChoiceFilter(field_name='has_malak',
                             choices=((True, 'Malak'), (False, 'No Malak')))

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def filter_has_dr(self, queryset, name, value):
        return queryset.filter(has_dr=value)

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def filter_has_malak(self, queryset, name, value):
        return queryset.filter(has_malak=value)

    class Meta:
        model = Player
        fields = ['has_dr', 'has_malak']


class GeoTBPlayerView(MetadataMixin, SingleTableMixin, FilterView):
    table_class = GeoTBPlayerTable
    model = Player
    template_name = 'sqds_officers/geotb_player_list.html'
    filterset_class = DRMalakFilterSet
    table_pagination = False

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # noinspection PyAttributeOutsideInit
        self.guild = Guild.objects.get(api_id=self.kwargs['api_id'])

    def get_queryset(self):
        qs = self.model.objects.filter(guild__api_id=self.guild.api_id)

        # ANNOTATE HAS DR/MALAK
        dr_player_ids = (PlayerUnit.objects
                         .filter(unit__api_id='DARTHREVAN',
                                 player__guild__api_id=self.guild.api_id)
                         .values('player__pk'))
        malak_player_ids = (PlayerUnit.objects
                            .filter(unit__api_id='DARTHMALAK',
                                    player__guild__api_id=self.guild.api_id)
                            .values('player__pk'))

        qs = qs.annotate(
            has_dr=Case(
                When(pk__in=dr_player_ids, then=True),
                default=False,
                output_field=BooleanField()),
            has_malak=Case(
                When(pk__in=malak_player_ids, then=True),
                default=False,
                output_field=BooleanField()))

        # ANNOTATE FACTION GP
        factions = {
            'profession_bountyhunter': {'label': 'bh_gp'},
            'affiliation_firstorder': {'label': 'fo_gp'},
            'affiliation_separatist': {'label': 'sep_gp'},
            'affiliation_nightsisters': {'label': 'ns_gp'},
        }
        for faction in factions:
            factions[faction]['id_list'] = Unit.objects.filter(
                categories__api_id=faction).values('id')

        for faction in factions:
            args = {
                factions[faction]['label']: Sum(
                    'unit_set__gp',
                    filter=Q(unit_set__unit__id__in=factions[faction]['id_list']))
            }

            qs = qs.annotate(**args)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_meta_title(self, **kwargs):
        return 'GeoTB player list'

    def get_meta_description(self, context=None):
        return f"GeoTB analysis page for {self.guild.name}"


##########################################################################################
## SEPARATIST FARM PROGRESS VIEW                                                        ##
##########################################################################################


class SepFarmProgressView(MetadataMixin, TemplateView):
    template_name = 'sqds_officers/sep_farm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sep_farm_graph'] = self.get_sep_farm_graph()
        return context

    # noinspection PyMethodMayBeStatic
    def get_sep_farm_graph(self):
        subquery = (GP.objects
                    .filter(player_api_id=OuterRef('api_id'),
                            unit__categories__api_id='affiliation_separatist')
                    .annotate(created_date=TruncDay('created'))
                    .values('created_date')
                    .annotate(gp=Sum('gp'))
                    .values('gp'))

        qs = (Player.objects
              .filter(guild__api_id=self.kwargs['api_id'])
              .annotate(start_gp=Subquery(subquery.order_by('created_date')[:1]))
              .annotate(end_gp=Subquery(subquery.order_by('-created_date')[:1]))
              .values('name', 'start_gp', 'end_gp'))

        df = pd.DataFrame(qs).sort_values(by='end_gp', ascending=False)
        df['diff'] = df['end_gp'] - df['start_gp']

        traces = [
            go.Bar(
                x=df['name'],
                y=df['start_gp'],
                name='June 21st'
            ),
            go.Bar(
                x=df['name'],
                y=df['diff'],
                name='Improvement'
            )
        ]

        layout = go.Layout(
            yaxis={'title': 'Separatists total GP'},
            barmode='stack',
            showlegend=False,
            height=600,
            margin=go.layout.Margin(l=60, r=10, b=130, t=40, pad=4)
        )
        figure = go.Figure(data=traces, layout=layout)
        return opy.plot(figure, auto_open=False, output_type='div')
