from django.db.models import Sum, Q, Case, When, BooleanField
from django_filters import FilterSet, ChoiceFilter
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from meta.views import MetadataMixin

from sqds.models import Player, Unit, PlayerUnit
from .tables import GeoTBPlayerTable


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

    def get_queryset(self):
        qs = self.model.objects.filter(guild__api_id='G2737841003')

        # ANNOTATE HAS DR/MALAK
        dr_player_ids = (PlayerUnit.objects
                         .filter(unit__api_id='DARTHREVAN',
                                 player__guild__api_id='G2737841003')
                         .values('player__pk'))
        malak_player_ids = (PlayerUnit.objects
                            .filter(unit__api_id='DARTHMALAK',
                                    player__guild__api_id='G2737841003')
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

    def get_meta_description(self, **kwargs):
        return "GeoTB analysis page for PREPARE's officers"
