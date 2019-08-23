from sqds_medals.models import MedaledUnit
from sqds.tables import RowCounterTable


class MedaledUnitTable(RowCounterTable):
    class Meta:
        model = MedaledUnit
        order_by = 'name'
        fields = ('name',)
