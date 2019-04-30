from django import template

from .sqds_filters import big_number

register = template.Library()


def compute_data_and_classes(data1, data2, filter=None):
    if data1 > data2:
        output_dict = {'left_class': 'success', 'right_class': 'danger'}
    elif data2 > data1:
        output_dict = {'left_class': 'danger', 'right_class': 'success'}
    else:
        output_dict = {'left_class': '', 'right_class': ''}

    if filter is not None:
        output_dict['left_data'] = filter(data1)
        output_dict['right_data'] = filter(data2)
    else:
        output_dict['left_data'] = data1
        output_dict['right_data'] = data2

    return output_dict


@register.inclusion_tag('sqds/player_compare_table.html')
def player_comparison(player1, player2):
    return {
        'player1': player1,
        'player2': player2,
        'lines': [
            {
                'label': 'GP', 'label_type': 'th',
                **compute_data_and_classes(player1.gp, player2.gp, big_number)
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;characters', 'label_type': 'td',
                **compute_data_and_classes(player1.gp_char, player2.gp_char,
                                           big_number)
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;ship', 'label_type': 'td',
                **compute_data_and_classes(player1.gp_ship, player2.gp_ship,
                                           big_number)
            },
            {
                'label': 'Zeta', 'label_type': 'th',
                **compute_data_and_classes(player1.zeta_count(),
                                           player2.zeta_count())
            },
            {
                'label': 'Unit count', 'label_type': 'th',
                **compute_data_and_classes(player1.unit_count(),
                                           player2.unit_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;7*', 'label_type': 'td',
                **compute_data_and_classes(player1.seven_star_unit_count(),
                                           player2.seven_star_unit_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;G12', 'label_type': 'td',
                **compute_data_and_classes(player1.g12_unit_count(),
                                           player2.g12_unit_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;G11', 'label_type': 'td',
                **compute_data_and_classes(player1.g11_unit_count(),
                                           player2.g11_unit_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;G10', 'label_type': 'td',
                **compute_data_and_classes(player1.g10_unit_count(),
                                           player2.g10_unit_count())
            },
            {
                'label': 'G12 gear pieces', 'label_type': 'th',
                **compute_data_and_classes(player1.g12_gear_count(),
                                           player2.g12_gear_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;left', 'label_type': 'td',
                **compute_data_and_classes(player1.left_hand_g12_gear_count(),
                                           player2.left_hand_g12_gear_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;right', 'label_type': 'td',
                **compute_data_and_classes(player1.right_hand_g12_gear_count(),
                                           player2.right_hand_g12_gear_count())
            },
            {
                'label': 'Mod count', 'label_type': 'th',
                **compute_data_and_classes(player1.mod_count(),
                                           player2.mod_count())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;+25', 'label_type': 'td',
                **compute_data_and_classes(player1.mod_count_speed_25(),
                                           player2.mod_count_speed_25())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;+20', 'label_type': 'td',
                **compute_data_and_classes(player1.mod_count_speed_20(),
                                           player2.mod_count_speed_20())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;+15', 'label_type': 'td',
                **compute_data_and_classes(player1.mod_count_speed_15(),
                                           player2.mod_count_speed_15())
            },
            {
                'label': '&nbsp;&nbsp;&nbsp;+10', 'label_type': 'td',
                **compute_data_and_classes(player1.mod_count_speed_10(),
                                           player2.mod_count_speed_10())
            },
        ]
    }
