"""Регистрация моделей приложения рецепты в админке."""
from django.contrib import admin
from django.db.models import Count

from .models import Ingredient, Recipe, ShoppingCart, Tag


admin.site.register(ShoppingCart)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Регистрация тэга в админке."""

    list_display = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Регистрация рецепта в админке."""

    def get_queryset(self, request):
        """Аннотация рецептов для подсчета."""
        return super().get_queryset(request).annotate(
            favorited_count=Count('favourite_recipe')
        )

    def favorited_count(self, obj):
        """Подсчет добавлений рецепта в избранное."""
        return obj.favorited_count

    favorited_count.short_description = 'Количество добавлений в избранное'
    favorited_count.admin_order_field = 'favorited_count'

    list_display = ('name', 'author', 'favorited_count')
    list_filter = ('tags', 'author')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Регистрация ингредиента в админке."""

    search_fields = ('name',)
    list_display = ('name', 'measurement_units')
    list_filter = ('name',)
