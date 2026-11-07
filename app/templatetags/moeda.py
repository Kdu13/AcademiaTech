from django import template

from app.services import formatar_brl


register = template.Library()


@register.filter
def moeda_brl(valor):
    return formatar_brl(valor)
