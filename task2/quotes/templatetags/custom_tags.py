from django import template

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()

@register.filter
def split_by_comma(value):
    """Розділяє рядок тегів за комами та прибирає зайві пробіли."""
    if not value:
        return []
    return [tag.strip() for tag in value.split(',') if tag.strip()]