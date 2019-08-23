from django_tables2 import SingleTableView
from meta.views import MetadataMixin

from .models import MedaledUnit
from .tables import MedaledUnitTable


class MedalList(MetadataMixin, SingleTableView):
    model = MedaledUnit
    table_class = MedaledUnitTable
    template_name = 'sqds_medals/medal_list.html'

    def get_meta_title(self, **kwargs):
        # TODO: implement this
        return ""

    def get_meta_description(self, context=None):
        # TODO: implement this
        return ""
