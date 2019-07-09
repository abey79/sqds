from django import template
from django.utils.html import format_html

from ..models import PlayerUnit

register = template.Library()

GEAR_TO_TEXT = {
    1: 'I',
    2: 'II',
    3: 'III',
    4: 'IV',
    5: 'V',
    6: 'VI',
    7: 'VII',
    8: 'VIII',
    9: 'IX',
    10: 'X',
    11: 'XI',
    12: 'XII',
    13: 'XIII'
}


@register.simple_tag
def char_portrait(pu: PlayerUnit):
    rarity_string = str()
    for i in range(1, 8):
        inactive_string = 'star-inactive' if i > pu.rarity else ''
        rarity_string += f'<div class="star star{i} {inactive_string}"></div>'
    zeta_string = str()
    zeta = pu.zeta_count
    if zeta > 0:
        zeta_string = f'<div class="char-portrait-full-zeta">{zeta}</div>'
    return format_html(f'''
        <div class="char-portrait-full char-portrait-full-gear-t{pu.gear}">
               <img class="char-portrait-full-img"
                   src="https://swgoh.gg/game-asset/u/{pu.unit.api_id}/"
                   alt="{pu.unit.name}" height="80" width="80">
               <div class="char-portrait-full-gear"></div>
               {rarity_string}
               {zeta_string}
               <div class="char-portrait-full-level">{pu.level}</div>
               <div class="char-portrait-full-gear-level">{GEAR_TO_TEXT[pu.gear]}</div>
        </div>''')
