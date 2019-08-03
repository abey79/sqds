from django import template
from django.utils.html import format_html

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


def generate_portrait_html(pu):
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
                       src="https://swgoh.gg/game-asset/u/{pu.unit_api_id}/"
                       alt="{pu.unit_name}" height="80" width="80">
                   <div class="char-portrait-full-gear"></div>
                   {rarity_string}
                   {zeta_string}
                   <div class="char-portrait-full-level">{pu.level}</div>
                   <div class="char-portrait-full-gear-level">{GEAR_TO_TEXT[
        pu.gear]}</div>
            </div>''')


def generate_empty_portrait_html():
    # TODO: a nice display would be desirable
    return format_html('''
                <div class="char-portrait-full">
                 <img class="char-portrait-full-img"></img>
                </div>''')


def normalise_related_data(pu):
    if not hasattr(pu, 'unit_name'):
        pu.unit_name = pu.unit.name
    if not hasattr(pu, 'unit_api_id'):
        pu.unit_api_id = pu.unit.api_id
    if not hasattr(pu, 'player_name'):
        pu.player_name = pu.player.name
    if not hasattr(pu, 'player_ally_code'):
        pu.player_ally_code = pu.player.ally_code
    return pu


@register.simple_tag
def char_portrait(pu):
    """
    Generate a portrait icon for the provided player unit. The pu parameter must be a
    PlayerUnit model or a compatible object. For better compatibility, the code first
    checks if attribute 'player_name', 'unit_name' and 'unit_api_id' exists. If so they
    are used. Otherwise, 'player.name', 'unit.name', and 'unit.api_id', are used,
    respectively.
    :param pu: the player unit
    :return: HTML of the portrait
    """
    if pu is None:
        return generate_empty_portrait_html()
    else:
        return generate_portrait_html(normalise_related_data(pu))


@register.inclusion_tag('sqds/char_portrait_with_stat.html')
def char_portrait_with_stat(pu):
    if pu is not None:
        pu = normalise_related_data(pu)

    context = {
        'portrait_html': generate_portrait_html(
            pu) if pu is not None else generate_empty_portrait_html(),
        'player_unit': pu,
    }
    return context
