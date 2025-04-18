from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to retrieve an item from a dictionary using the specified key.
    
    Usage in template:
    {{ dictionary|get_item:key }}
    """
    return dictionary.get(key) 