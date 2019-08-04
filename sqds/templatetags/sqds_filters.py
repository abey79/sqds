import locale
from textwrap import wrap

from django import template

locale.setlocale(locale.LC_ALL, '')
register = template.Library()


@register.filter
def big_number(num):
    try:
        num = float(num)
    except (ValueError, TypeError):
        num = 0

    num = int(round(float(num), 0))
    return '{0:n}'.format(num)


@register.filter
def ally_code(num):
    return '-'.join(wrap(str(num), 3))


@register.filter
def percent(num):
    return '{:0.1f}%'.format(num * 100)


@register.filter
def number_kilo(num):
    try:
        num = float(num)
    except ValueError:
        num = 0

    if num < 100:
        return '{:0.0f}'.format(num)
    else:
        return '{:0.1f}k'.format(num / 1000)
