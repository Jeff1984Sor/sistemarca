# casos/templatetags/custom_filters.py

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def split(value, key):
    """
    Filtro de template que quebra uma string por um separador.
    Uso: {{ algum_texto|split:"||" }}
    """
    try:
        return value.split(key)
    except:
        return [value] # Retorna a string original em uma lista se algo der errado

@register.filter
def replace(value, args):
    """
    Substitui uma substring por outra.
    Uso: {{ algum_texto|replace:"texto_antigo,texto_novo" }}
    """
    try:
        old_string, new_string = args.split(',')
        return value.replace(old_string, new_string)
    except:
        return value # Retorna o valor original se algo der errado

@register.filter
def splitlines(value):
    """
    Quebra uma string em uma lista de linhas.
    """
    try:
        return value.splitlines()
    except:
        return [value]

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='to_dot_decimal')
def to_dot_decimal(value):
    """
    Converte um valor decimal ou float para uma string com ponto como separador,
    adequado para o 'value' de um input type="number".
    """
    if value is None:
        return ''
    # Converte para string e substitui a vírgula por ponto
    return str(value).replace(',', '.')