from django import template

from ..models import ModSet
from .sqds_filters import percent

register = template.Library()

SLOT_TO_TEXT = {
    0: '■',
    1: '⬈',
    2: '◆',
    3: '▲',
    4: '●',
    5: '✚'
}

TIER_TO_TEXT = {
    1: 'E',
    2: 'D',
    3: 'C',
    4: 'B',
    5: 'A'
}

PIPS_TO_TEXT = {
    1: 'Mk I',
    2: 'Mk II',
    3: 'Mk III',
    4: 'Mk IV',
    5: 'Mk V',
    6: 'Mk VI'
}

STATS = {
    'speed': {'label': 'Speed', 'filter': None},
    'health': {'label': 'Health', 'filter': None},
    'health_percent': {'label': 'Health', 'filter': percent},
    'protection': {'label': 'Protection', 'filter': None},
    'protection_percent': {'label': 'Protection', 'filter': percent},
    'offense': {'label': 'Offense', 'filter': None},
    'offense_percent': {'label': 'Offense', 'filter': percent},
    'defense': {'label': 'Defense', 'filter': None},
    'defense_percent': {'label': 'Defense', 'filter': percent},
    'critical_chance': {'label': 'Critical Chance', 'filter': percent},
    'critical_damage': {'label': 'Critical Damage', 'filter': percent},
    'potency': {'label': 'Potency', 'filter': percent},
    'tenacity': {'label': 'Tenacity', 'filter': percent},
    'critical_avoidance': {'label': 'Critical avoidance', 'filter': percent},
    'accuracy': {'label': 'Accuracy', 'filter': percent}
}


@register.inclusion_tag('sqds/mod_widget.html')
def mod_widget(mod, show_unit_info=False):
    if mod is None:
        return {'mod': mod}

    stat_list = []
    for stat in STATS:
        value = getattr(mod, stat)

        if value == 0:
            continue

        if STATS[stat]['filter'] is not None:
            value_string = STATS[stat]['filter'](value)
        else:
            value_string = str(value)

        stat_list.append({
            'label': STATS[stat]['label'],
            'value': value_string})

    return {
        'mod': mod,
        'show_unit_info': show_unit_info,
        'player_unit': mod.player_unit,
        'set_text': ModSet.label(mod.mod_set),
        'slot_text': SLOT_TO_TEXT[mod.slot],
        'tier_text': TIER_TO_TEXT[mod.tier],
        'pips_text': PIPS_TO_TEXT[mod.pips],
        'stat_list': stat_list
    }
