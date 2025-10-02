# casos/templatetags/custom_filters.py

from django import template

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