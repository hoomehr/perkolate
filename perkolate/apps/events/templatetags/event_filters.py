from django import template
import random as random_module
from datetime import datetime, time

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key.
    Usage: {{ mydict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def split(value, delimiter):
    """
    Split a string by a delimiter and return a list.
    """
    return value.split(delimiter)

@register.filter
def random(value):
    """
    Return a random item from a list.
    """
    if isinstance(value, list) and len(value) > 0:
        return random_module.choice(value)
    return value

@register.filter
def filter_status(notes, status):
    """
    Filters a list of notes by status.
    Usage: {{ notes|filter_status:"completed" }}
    For multiple statuses: {{ notes|filter_status:"completed,in_progress" }}
    """
    statuses = status.split(',')
    return [note for note in notes if note.status in statuses]

@register.filter
def exclude_status(notes, status):
    """
    Excludes notes with the specified status.
    Usage: {{ notes|exclude_status:"completed" }}
    For multiple statuses: {{ notes|exclude_status:"completed,in_progress" }}
    """
    statuses = status.split(',')
    return [note for note in notes if note.status not in statuses]

@register.filter
def make_positive(value):
    """
    Return the absolute value of a number.
    """
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value

@register.filter
def hours_to_pixels(time_obj):
    """
    Convert a time object to vertical position in pixels for the weekly calendar.
    Each hour is 60px tall.
    """
    if isinstance(time_obj, str):
        try:
            time_obj = datetime.strptime(time_obj, '%H:%M:%S').time()
        except ValueError:
            try:
                time_obj = datetime.strptime(time_obj, '%H:%M').time()
            except ValueError:
                return 0
    
    if not isinstance(time_obj, time):
        return 0
    
    # Calculate minutes since start of day
    total_minutes = time_obj.hour * 60 + time_obj.minute
    
    # Convert to pixels (1 hour = 60px)
    return total_minutes / 60 * 60

@register.filter
def hours_to_height(duration):
    """
    Convert a duration in hours to a height in pixels for the weekly calendar.
    Each hour is 60px tall.
    """
    try:
        duration_float = float(duration)
        return duration_float * 60
    except (ValueError, TypeError):
        return 60  # Default to 1 hour height 