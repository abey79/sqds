import locale
from textwrap import wrap

from django import template

locale.setlocale(locale.LC_ALL, '')
register = template.Library()


def big_number(num):
    try:
        num = float(num)
    except ValueError:
        num = 0

    num = int(round(float(num), 0))
    return '{0:n}'.format(num)


def ally_code(num):
    return '-'.join(wrap(str(num), 3))


register.filter('big_number', big_number)
register.filter('ally_code', ally_code)
