from django import template
from django.utils.html import format_html

from sqds.models import ModSet

register = template.Library()

SLOT_TO_TEXT = {
    0: {'ui': '■', 'css': 'square'},
    1: {'ui': '⬈', 'css': 'arrow'},
    2: {'ui': '◆', 'css': 'diamond'},
    3: {'ui': '▲', 'css': 'triangle'},
    4: {'ui': '●', 'css': 'circle'},
    5: {'ui': '✚', 'css': 'cross'},
}

TIER_TO_TEXT = {
    1: {'ui': 'E', 'css': 'e'},
    2: {'ui': 'D', 'css': 'd'},
    3: {'ui': 'C', 'css': 'c'},
    4: {'ui': 'B', 'css': 'b'},
    5: {'ui': 'A', 'css': 'a'},
}

PIPS_TO_TEXT = {
    1: 'Mk I',
    2: 'Mk II',
    3: 'Mk III',
    4: 'Mk IV',
    5: 'Mk V',
    6: 'Mk VI'
}

SET_TO_CSS = {
    ModSet.HEALTH: 'hp',
    ModSet.OFFENSE: 'off',
    ModSet.DEFENSE: 'def',
    ModSet.SPEED: 'sp',
    ModSet.CRITICAL_CHANCE: 'cc',
    ModSet.CRITICAL_DAMAGE: 'cd',
    ModSet.POTENCY: 'pot',
    ModSet.TENACITY: 'ten',
}

def mod_percent(f):
    return f'{f:0.2%}'

STATS = {
    'speed': {'label': 'Speed', 'filter': None},
    'health': {'label': 'Health', 'filter': None},
    'health_percent': {'label': 'Health', 'filter': mod_percent},
    'protection': {'label': 'Protection', 'filter': None},
    'protection_percent': {'label': 'Protection', 'filter': mod_percent},
    'offense': {'label': 'Offense', 'filter': None},
    'offense_percent': {'label': 'Offense', 'filter': mod_percent},
    'defense': {'label': 'Defense', 'filter': None},
    'defense_percent': {'label': 'Defense', 'filter': mod_percent},
    'critical_chance': {'label': 'Critical Chance', 'filter': mod_percent},
    'critical_damage': {'label': 'Critical Damage', 'filter': mod_percent},
    'potency': {'label': 'Potency', 'filter': mod_percent},
    'tenacity': {'label': 'Tenacity', 'filter': mod_percent},
    'critical_avoidance': {'label': 'Critical avoidance', 'filter': mod_percent},
    'accuracy': {'label': 'Accuracy', 'filter': mod_percent}
}


@register.simple_tag
def mod_icon(mod):
    return format_html(
        '<div class="mod mod-{slot}-{tier}{ext}">'
        '   <div class="mod-set mod-{set}-{tier}">'
        '   </div>'
        '</div>',
        slot=SLOT_TO_TEXT[mod.slot]['css'], tier=TIER_TO_TEXT[mod.tier]['css'],
        set=SET_TO_CSS[mod.mod_set], ext='-6pips' if mod.pips == 6 else '')


@register.inclusion_tag('sqds/mod_widget.html')
def mod_widget(mod, show_unit_info=False):
    if mod is None:
        return {'mod': mod}

    stat_list = []
    for stat in STATS:
        value = getattr(mod, stat)
        rolls = getattr(mod, stat + '_roll')

        if value == 0:
            continue

        if STATS[stat]['filter'] is not None:
            value_string = STATS[stat]['filter'](value)
        else:
            value_string = str(value)

        item = {
            'label': STATS[stat]['label'],
            'value': value_string
        }
        if stat == mod.get_primary_stat_display():
            stat_list.insert(0, item)
        else:
            item['label'] += f' ({rolls})'
            stat_list.append(item)

    return {
        'mod': mod,
        'show_unit_info': show_unit_info,
        'player_unit': mod.player_unit,
        'set_text': ModSet.label(mod.mod_set),
        'slot_text': SLOT_TO_TEXT[mod.slot]['ui'],
        'tier_text': TIER_TO_TEXT[mod.tier]['ui'],
        'pips_text': PIPS_TO_TEXT[mod.pips],
        'stat_list': stat_list,
        'pips_loop': range(mod.pips),
    }
