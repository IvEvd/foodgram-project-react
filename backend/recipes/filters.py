"""Фильтры для приложения api."""

from django.db.models import Value, When, Case, Q, IntegerField
from django_filters import rest_framework as djangofilters


class IngredientFilter(djangofilters.FilterSet):
    """Фильтр ингредиентов."""

    def filter_queryset(self, queryset):
        """Фильтр ингредиентов.

        Фильтрует выдачу по полю имени по началу и вхождению,
        раньше в выдаче находятся элементы с совпадающим
        началом
        """
        name = self.data.get('name')
        if not name:
            return queryset
        else:
            queryset = queryset.annotate(
                starts_with_search=Case(
                    When(name__startswith=name, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField()
                ),
                contains_search=Case(
                    When(name__icontains=name, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField())
            ).filter(Q(starts_with_search=0) | Q(contains_search=0)
                     ).order_by('starts_with_search',
                                'contains_search', 'name'
                                )
            return queryset
