import locale
from textwrap import wrap

from django.db.models import Count, Sum, Q

import django_tables2 as tables
from django_tables2.utils import A

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
        return '{0:n}'.format(value) if value != 0 else '-'


class AllyCodeColumn(tables.Column):
    def render(self, value):
        return '-'.join(wrap(str(value), 3))


class PercentColumn(tables.Column):
    def __init__(self, **kwargs):
        nested_set(kwargs, ['attrs', 'td', 'style'], 'text-align: right;')
        super(PercentColumn, self).__init__(**kwargs)

    def render(self, value):
        return '{:0.1f}%'.format(value * 100)


class PlayerTable(tables.Table):
    name = tables.LinkColumn('sqds:player', args=[A('ally_code')])
    guild = tables.LinkColumn('sqds:guild', args=[A('guild.api_id')])
    ally_code = AllyCodeColumn()

    gp = LargeIntColumn()
    gp_char = LargeIntColumn()
    gp_ship = LargeIntColumn()

    unit_count = LargeIntColumn('Characters', initial_sort_descending=True)
    seven_star_unit_count = LargeIntColumn('7*', initial_sort_descending=True)
    g12_unit_count = LargeIntColumn('G12', initial_sort_descending=True)
    g11_unit_count = LargeIntColumn('G11', initial_sort_descending=True)
    g10_unit_count = LargeIntColumn('G10', initial_sort_descending=True)

    mod_count_speed_25 = LargeIntColumn('+25', initial_sort_descending=True)
    mod_count_speed_20 = LargeIntColumn('+20', initial_sort_descending=True)
    mod_count_speed_15 = LargeIntColumn('+15', initial_sort_descending=True)
    mod_count_speed_10 = LargeIntColumn('+10', initial_sort_descending=True)

    mod_total_speed_15plus = LargeIntColumn('∑15+',
                                            initial_sort_descending=True)

    zeta_count = LargeIntColumn(initial_sort_descending=True)
    right_hand_g12_gear_count = LargeIntColumn('G12+ pces',
                                               initial_sort_descending=True)

    def generic_order_unit_count(self, query_set, is_descending, gear_level):
        query_set = query_set.annotate(
            _unit_count=Count('unit_set', filter=Q(unit_set__gear=gear_level))
        ).order_by(('-' if is_descending else '') + '_unit_count')
        return (query_set, True)

    def order_g12_unit_count(self, query_set, is_descending):
        return self.generic_order_unit_count(query_set, is_descending, 12)

    def order_g11_unit_count(self, query_set, is_descending):
        return self.generic_order_unit_count(query_set, is_descending, 11)

    def order_g10_unit_count(self, query_set, is_descending):
        return self.generic_order_unit_count(query_set, is_descending, 10)

    def order_unit_count(self, query_set, is_descending):
        query_set = query_set.annotate(
            _unit_count=Count('unit_set')
        ).order_by(('-' if is_descending else '') + '_unit_count')
        return (query_set, True)

    def order_seven_star_unit_count(self, query_set, is_descending):
        query_set = query_set.annotate(
            _7_unit_count=Count(
                'unit_set',
                filter=Q(unit_set__rarity=7))
        ).order_by(('-' if is_descending else '') + '_7_unit_count')
        return (query_set, True)

    def order_right_hand_g12_gear_count(self, query_set, is_descending):
        query_set = query_set.annotate(
            _rh_g12_count=Count(
                'unit_set__gear_set',
                filter=Q(unit_set__gear_set__gear__is_right_hand_g12=True))
        ).order_by(('-' if is_descending else '') + '_rh_g12_count')
        return (query_set, True)

    def order_zeta_count(self, query_set, is_descending):
        query_set = query_set.annotate(
            _zeta_count=Count('unit_set__zeta_set')
        ).order_by(('-' if is_descending else '') + '_zeta_count')
        return (query_set, True)

    def generic_order_mod_count_speed(self, query_set, is_descending,
                                      min_value, max_value):
        query_set = query_set.annotate(
            _mod_count=Count(
                'unit_set__mod_set',
                filter=(~Q(unit_set__mod_set__slot=1)
                        & Q(unit_set__mod_set__speed__gte=min_value)
                        & Q(unit_set__mod_set__speed__lte=max_value)))
        ).order_by(('-' if is_descending else '') + '_mod_count')
        return (query_set, True)

    def order_mod_count_speed_25(self, query_set, is_descending):
        return self.generic_order_mod_count_speed(
            query_set, is_descending, 25, 100)

    def order_mod_count_speed_20(self, query_set, is_descending):
        return self.generic_order_mod_count_speed(
            query_set, is_descending, 20, 24)

    def order_mod_count_speed_15(self, query_set, is_descending):
        return self.generic_order_mod_count_speed(
            query_set, is_descending, 15, 19)

    def order_mod_count_speed_10(self, query_set, is_descending):
        return self.generic_order_mod_count_speed(
            query_set, is_descending, 15, 19)

    def order_mod_total_speed_15plus(self, query_set, is_descending):
        query_set = query_set.annotate(
            _mod_sum=Sum(
                'unit_set__mod_set__speed',
                filter=(~Q(unit_set__mod_set__slot=1)
                        & Q(unit_set__mod_set__speed__gte=15)))
        ).order_by(('-' if is_descending else '') + '_mod_sum')
        return (query_set, True)

    class Meta:
        model = Player
        fields = ('name', 'guild', 'ally_code',
                  'level', 'gp', 'gp_char', 'gp_ship', 'unit_count',
                  'seven_star_unit_count', 'g12_unit_count', 'g11_unit_count',
                  'g10_unit_count', 'right_hand_g12_gear_count', 'zeta_count',
                  'mod_count_speed_25', 'mod_count_speed_20',
                  'mod_count_speed_15', 'mod_count_speed_10',
                  'mod_total_speed_15plus')


class PlayerUnitTable(tables.Table):
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

    def order_zeta_summary(self, query_set, is_descending):
        query_set = query_set.annotate(
            _zeta_count=Count('zeta_set')
        ).order_by(('-' if is_descending else '') + '_zeta_count')
        return (query_set, True)

    class Meta:
        model = PlayerUnit
        order_by = '-gp'
        sequence = ('unit', 'player', 'gp', 'summary', 'zeta_summary', '...')
        exclude = ('id', 'rarity', 'level', 'gear',
                   'equipped_count', 'armor_penetration',
                   'resistance_penetration', 'health_steal', 'last_updated')
