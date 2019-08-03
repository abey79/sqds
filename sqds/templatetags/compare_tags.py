from django import template

from .sqds_filters import big_number

register = template.Library()


def compute_data_and_classes(values, data_filter=None):
    """
    Returns a list of dict in the form [{'value': val, 'class': 'success']]
    :param values: Values to process. Min and max are assigned corresponding classes.
    :param data_filter: If not None, applied on all values before output
    :return: processed array of dict
    """
    output_values = []
    max_value = max(values)
    min_value = min(values)

    for idx, value in enumerate(values):
        val = {}
        if value == min_value and value != max_value:
            val['class'] = 'danger'
        elif value == max_value and value != min_value:
            val['class'] = 'success'
        else:
            val['class'] = ''

        val['value'] = data_filter(value) if data_filter else value

        output_values.append(val)

    return output_values


@register.inclusion_tag('sqds/player_compare_table.html')
def player_comparison(players):
    context = {
        'players': players,
        'lines': [
            {
                'label': '<th>GP</th>',
                'data': compute_data_and_classes([p.gp for p in players], big_number)
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;characters</td>',
                'data': compute_data_and_classes([p.gp_char for p in players], big_number)
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;ship</td>',
                'data': compute_data_and_classes([p.gp_ship for p in players], big_number)
            },
            {
                'label': '<th>Zeta</th>',
                'data': compute_data_and_classes([p.zeta_count for p in players])
            },
            {
                'label': '<th>Unit count</th>',
                'data': compute_data_and_classes([p.unit_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;7*</td>',
                'data': compute_data_and_classes(
                    [p.seven_star_unit_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;G13</td>',
                'data': compute_data_and_classes([p.g13_unit_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;G12</td>',

                'data': compute_data_and_classes([p.g12_unit_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;G11</td>',

                'data': compute_data_and_classes([p.g11_unit_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;G10</td>',
                'data': compute_data_and_classes([p.g10_unit_count for p in players])
            },
            {
                'label': '<th>G12 gear pieces</th>',
                'data': compute_data_and_classes([p.g12_gear_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;left</td>',
                'data': compute_data_and_classes(
                    [p.left_hand_g12_gear_count for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;right</td>',
                'data': compute_data_and_classes(
                    [p.right_hand_g12_gear_count for p in players])
            },
            {
                'label': '<th>Mod count</th>',
                'data': [''] * len(players)
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;+25</td>',
                'data': compute_data_and_classes([p.mod_count_speed_25 for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;+20</td>',
                'data': compute_data_and_classes([p.mod_count_speed_20 for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;+15</td>',
                'data': compute_data_and_classes([p.mod_count_speed_15 for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;+10</td>',
                'data': compute_data_and_classes([p.mod_count_speed_10 for p in players])
            },
            {
                'label': '<td>&nbsp;&nbsp;&nbsp;∑15+</td>',
                'data': compute_data_and_classes(
                    [p.mod_total_speed_15plus for p in players])
            },
        ]
    }

    return context
