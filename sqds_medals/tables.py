import django_tables2 as tables
from django.utils.html import format_html

from sqds.models import Unit
from sqds.tables import RowCounterTable


# noinspection PyMethodMayBeStatic
class MedaledUnitTable(RowCounterTable):
    name = tables.Column()
    stat_rules = tables.Column("Stat Rules", empty_values=(), orderable=False)
    zeta_rules = tables.Column("Zeta Rules", empty_values=(), orderable=False)

    def render_stat_rules(self, record):
        return format_html(
            "<ul>{}</ul>",
            "".join(f"<li>{str(r)}</li>" for r in record.stat_medal_rule_set.all()),
        )

    def render_zeta_rules(self, record):
        return format_html(
            "<ul>{}</ul>",
            "".join(
                f"<li>{r.skill.name}</li>" for r in record.zeta_medal_rule_set.all()
            ),
        )

    class Meta:
        model = Unit
        order_by = "name"
        fields = ("row_counter", "name", "stat_rules", "zeta_rules")
