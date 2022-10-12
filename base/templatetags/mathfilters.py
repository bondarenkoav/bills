__author__ = 'https://github.com/dbrgn/django-mathfilters'

# -*- coding: utf-8 -*-
#from __future__ import print_function, division, absolute_import, unicode_literals

# sub – subtraction
# mul – multiplication
# div – division
# intdiv – integer (floor) division
# abs – absolute value
# mod – modulo
# addition – replacement for the add filter with support for float / decimal types

# <ul>
#     <li>8 + 3 = {{ 8|add:3 }}</li>
#     <li>13 - 17 = {{ 13|sub:17 }}</li>
#
#     {% with answer=42 %}
#     <li>42 * 0.5 = {{ answer|mul:0.5 }}</li>
#     {% endwith %}
#
#     {% with numerator=12 denominator=3 %}
#     <li>12 / 3 = {{ numerator|div:denominator }}</li>
#     {% endwith %}
#
#     <li>|-13| = {{ -13|abs }}</li>
# </ul>

import logging
try:
    from cdecimal import Decimal
except ImportError:
    from decimal import Decimal

from django.template import Library


register = Library()
logger = logging.getLogger(__name__)


def valid_numeric(arg):
    if isinstance(arg, (int, float, Decimal)):
        return arg
    try:
        return int(arg)
    except ValueError:
        return float(arg)


def handle_float_decimal_combinations(value, arg, operation):
    if isinstance(value, float) and isinstance(arg, Decimal):
        logger.warning('Unsafe operation: {0!r} {1} {2!r}.'.format(value, operation, arg))
        value = Decimal(str(value))
    if isinstance(value, Decimal) and isinstance(arg, float):
        logger.warning('Unsafe operation: {0!r} {1} {2!r}.'.format(value, operation, arg))
        arg = Decimal(str(arg))
    return value, arg


@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '-')
        return nvalue - narg
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return ''
sub.is_safe = False


@register.filter
def mul(value, arg):
    """Multiply the arg with the value."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '*')
        return nvalue * narg
    except (ValueError, TypeError):
        try:
            return value * arg
        except Exception:
            return ''
mul.is_safe = False


@register.filter
def div(value, arg):
    """Divide the arg by the value."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '/')
        return nvalue / narg
    except (ValueError, TypeError):
        try:
            return value / arg
        except Exception:
            return ''
div.is_safe = False


@register.filter
def intdiv(value, arg):
    """Divide the arg by the value. Use integer (floor) division."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '//')
        return nvalue // narg
    except (ValueError, TypeError):
        try:
            return value // arg
        except Exception:
            return ''
intdiv.is_safe = False


@register.filter(name='abs')
def absolute(value):
    """Return the absolute value."""
    try:
        return abs(valid_numeric(value))
    except (ValueError, TypeError):
        try:
            return abs(value)
        except Exception:
            return ''
absolute.is_safe = False


@register.filter
def mod(value, arg):
    """Return the modulo value."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '%')
        return nvalue % narg
    except (ValueError, TypeError):
        try:
            return value % arg
        except Exception:
            return ''
mod.is_safe = False


@register.filter(name='addition')
def addition(value, arg):
    """Float-friendly replacement for Django's built-in `add` filter."""
    try:
        nvalue, narg = handle_float_decimal_combinations(
            valid_numeric(value), valid_numeric(arg), '+')
        return nvalue + narg
    except (ValueError, TypeError):
        try:
            return value + arg
        except Exception:
            return ''
addition.is_safe = False