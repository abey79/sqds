import locale

import django_tables2 as tables

from .models import Player, PlayerUnit


locale.setlocale(locale.LC_ALL, '')


# based on https://stackoverflow.com/a/13688108/229511
def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


class LargeIntColumn(tables.Column):
    def __init__(self, **kwargs):
        nested_set(kwargs, ['attrs', 'td', 'style'], 'text-align: right;')
        super(LargeIntColumn, self).__init__(**kwargs)

    def render(self, value):
        return '{0:n}'.format(value) if value != 0 else '-'


class PercentColumn(tables.Column):
    def __init__(self, **kwargs):
        nested_set(kwargs, ['attrs', 'td', 'style'], 'text-align: right;')
        super(PercentColumn, self).__init__(**kwargs)

    def render(self, value):
        return '{:0.1f}%'.format(value * 100)


class PlayerTable(tables.Table):
    gp = LargeIntColumn()
    gp_char = LargeIntColumn()
    gp_ship = LargeIntColumn()

    zeta_count = LargeIntColumn(orderable=False)

    class Meta:
        model = Player
        sequence = ('name', 'guild', 'ally_code',
                    'level', 'gp', 'gp_char', 'gp_ship', 'zeta_count')
        exclude = ('id', 'api_id', 'last_updated')


class PlayerUnitTable(tables.Table):
    gp = LargeIntColumn(initial_sort_descending=True)

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
    zeta_summary = tables.Column('Zetas', orderable=False)

    class Meta:
        model = PlayerUnit
        sequence = ('unit', 'player', 'gp', 'summary', 'zeta_summary', '...')
        exclude = ('id', 'rarity', 'level', 'gear',
                   'equipped_count', 'armor_penetration',
                   'resistance_penetration', 'health_steal', 'last_updated')
