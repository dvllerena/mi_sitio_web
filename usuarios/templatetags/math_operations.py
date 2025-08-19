from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    return float(value) - float(arg)


@register.filter(name='subtract')
def subtract(value, arg):
    """Resta arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
    
@register.filter
def absolute(value):
    """Filtro para obtener valor absoluto"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value