import itertools
import locale
from textwrap import wrap

from django.db.models import Count

import django_tables2 as tables
from django_tables2.utils import A

from .utils import format_large_int
from .models import Player, PlayerUnit

locale.setlocale(locale.LC_ALL, '')


# based on https://stackoverflow.com/a/13688108/229511
def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


class LargeIntColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        # nested_set(kwargs, ['attrs', 'td', 'style'], 'text-align: right;')
        super(LargeIntColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        return format_large_int(value)


class AllyCodeColumn(tables.Column):
    def render(self, value):
        return '-'.join(wrap(str(value), 3))


class PercentColumn(tables.Column):
    def __init__(self, **kwargs):
        nested_set(kwargs, ['attrs', 'td', 'style'], 'text-align: right;')
        super(PercentColumn, self).__init__(**kwargs)

    def render(self, value):
        return '{:0.1f}%'.format(value * 100)


class RowCounterTable(tables.Table):
    row_counter = tables.Column('', empty_values=(), orderable=False, attrs={
        'td': {
            'style': 'color: #ddd'
        }})

    def render_row_counter(self):
        self.row_counter = getattr(
            self, 'row_counter',
            itertools.count(self.page.start_index() if hasattr(self, 'page') else 1))
        return next(self.row_counter)


class PlayerTable(RowCounterTable):
    name = tables.LinkColumn('sqds:player', args=[A('ally_code')], verbose_name='Player')
    guild_name = tables.LinkColumn('sqds:guild', args=[A('guild_api_id')],
                                   verbose_name='Guild')

    gp = LargeIntColumn()
    gp_char = LargeIntColumn()
    gp_ship = LargeIntColumn()

    unit_count = LargeIntColumn('Characters', initial_sort_descending=True)
    seven_star_unit_count = LargeIntColumn('7*', initial_sort_descending=True)
    g13_unit_count = LargeIntColumn('G13', initial_sort_descending=True)
    g12_unit_count = LargeIntColumn('G12', initial_sort_descending=True)
    g11_unit_count = LargeIntColumn('G11', initial_sort_descending=True)
    g10_unit_count = LargeIntColumn('G10', initial_sort_descending=True)

    mod_count_speed_25 = LargeIntColumn(
        '+25', initial_sort_descending=True,
        attrs={
            'th': {'data-toggle': 'tooltip',
                   'title': "Total number of 25+ speed secondaries"}})
    mod_count_speed_20 = LargeIntColumn(
        '+20', initial_sort_descending=True,
        attrs={
            'th': {'data-toggle': 'tooltip',
                   'title': "Total number of 20-24 speed secondaries"}})
    mod_count_speed_15 = LargeIntColumn(
        '+15', initial_sort_descending=True,
        attrs={
            'th': {'data-toggle': 'tooltip',
                   'title': "Total number of 15-19 speed secondaries"}})
    mod_count_speed_10 = LargeIntColumn(
        '+10', initial_sort_descending=True,
        attrs={
            'th': {'data-toggle': 'tooltip',
                   'title': "Total number of 10-14 speed secondaries"}})
    mod_total_speed_15plus = LargeIntColumn(
        '∑15+', initial_sort_descending=True,
        attrs={
            'th': {'data-toggle': 'tooltip',
                   'title': "Sum of all the speed secondaries equal or greater than 15"}})
    zeta_count = LargeIntColumn(initial_sort_descending=True)
    right_hand_g12_gear_count = LargeIntColumn(
        'G12+ pces', initial_sort_descending=True,
        attrs={'th': {'data-toggle': 'tooltip',
                      'title': "Total number of right-hand-side G12 pieces"}})
    sep_gp = LargeIntColumn(
        'Sep GP', initial_sort_descending=True,
        attrs={'td': {'class': 'danger'},
               'th': {'data-toggle': 'tooltip',
                      'title': "Sum of the GP of all Separatists"}})

    class Meta:
        model = Player
        fields = ('row_counter', 'name', 'guild_name',
                  'level', 'gp', 'gp_char', 'gp_ship', 'sep_gp', 'unit_count',
                  'seven_star_unit_count', 'g13_unit_count', 'g12_unit_count',
                  'g11_unit_count', 'g10_unit_count', 'right_hand_g12_gear_count',
                  'zeta_count', 'mod_count_speed_25', 'mod_count_speed_20',
                  'mod_count_speed_15', 'mod_count_speed_10',
                  'mod_total_speed_15plus')


class PlayerUnitTable(RowCounterTable):
    player = tables.Column(linkify=('sqds:player', {'ally_code': A('player.ally_code')}))

    gp = LargeIntColumn(initial_sort_descending=True)
    unit = tables.LinkColumn('sqds:unit', args=[A('id')])

    speed = LargeIntColumn(initial_sort_descending=True)
    health = LargeIntColumn(initial_sort_descending=True)
    protection = LargeIntColumn(initial_sort_descending=True)

    physical_damage = LargeIntColumn(initial_sort_descending=True)
    physical_crit_chance = PercentColumn(initial_sort_descending=True)
    special_damage = LargeIntColumn(initial_sort_descending=True)
    special_crit_chance = PercentColumn(initial_sort_descending=True)
    crit_damage = PercentColumn(initial_sort_descending=True)

    potency = PercentColumn(initial_sort_descending=True)
    tenacity = PercentColumn(initial_sort_descending=True)
    armor = PercentColumn(initial_sort_descending=True)
    resistance = PercentColumn(initial_sort_descending=True)
    health_steal = PercentColumn(initial_sort_descending=True)

    summary = tables.Column('Summary', initial_sort_descending=True,
                            order_by=['rarity', 'level', 'gear',
                                      'equipped_count'])
    zeta_summary = tables.Column('Zetas', initial_sort_descending=True)

    # noinspection PyMethodMayBeStatic
    def order_zeta_summary(self, query_set, is_descending):
        query_set = query_set.annotate(
            _zeta_count=Count('zeta_set')
        ).order_by(('-' if is_descending else '') + '_zeta_count')
        return query_set, True

    class Meta:
        model = PlayerUnit
        order_by = '-gp'
        sequence = ('row_counter', 'unit', 'player', 'gp', 'summary', 'zeta_summary',
                    '...')
        exclude = ('id', 'rarity', 'level', 'gear',
                   'equipped_count', 'armor_penetration',
                   'resistance_penetration', 'health_steal', 'last_updated')
