import django_tables2 as tables

from sqds.models import Player
from sqds.tables import RowCounterTable, LargeIntColumn


class GeoTBPlayerTable(RowCounterTable):
    name = tables.LinkColumn('sqds:player', args=[tables.A('ally_code')],
                             verbose_name='Player')

    has_dr = tables.BooleanColumn(verbose_name='Revan?', yesno="Y,-",
                                  initial_sort_descending=True)
    has_malak = tables.BooleanColumn(verbose_name='Malak?', yesno="Y,-",
                                     initial_sort_descending=True)

    sep_gp = LargeIntColumn('Sep', initial_sort_descending=True)
    bh_gp = LargeIntColumn('BH', initial_sort_descending=True)
    fo_gp = LargeIntColumn('FO', initial_sort_descending=True)
    ns_gp = LargeIntColumn('NS', initial_sort_descending=True)

    class Meta:
        model = Player
        fields = ('row_counter', 'name', 'has_dr', 'has_malak',
                  'sep_gp', 'bh_gp', 'fo_gp', 'ns_gp')
