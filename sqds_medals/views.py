from django.db.models import Count, F
from django_tables2 import SingleTableView
from meta.views import MetadataMixin

from sqds.models import Unit
from .tables import MedaledUnitTable


class MedalList(MetadataMixin, SingleTableView):
    model = Unit
    table_class = MedaledUnitTable
    template_name = 'sqds_medals/medal_list.html'

    def get_queryset(self):
        return (self.model
                .objects
                .annotate(stat_rule_count=Count('stat_medal_rule_set', distinct=True),
                          zeta_rule_count=Count('zeta_medal_rule_set', distinct=True),
                          tot_rule_count=F('stat_rule_count') + F('zeta_rule_count'))
                .filter(tot_rule_count=7)
                .prefetch_related('stat_medal_rule_set',
                                  'zeta_medal_rule_set',
                                  'zeta_medal_rule_set__skill'))

    def get_meta_title(self, **kwargs):
        # TODO: implement this
        return ""

    def get_meta_description(self, context=None):
        # TODO: implement this
        return ""
