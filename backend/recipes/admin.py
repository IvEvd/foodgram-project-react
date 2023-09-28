"""Регистрация моделей приложения рецепты в админке."""
from django.contrib import admin

from .models import Ingredient, Recipe, ShoppingCart, Tag


admin.site.register(ShoppingCart)


@admin.register(Tag)
class MyModelAdmin(admin.ModelAdmin):
    """Регистрация тэга в админке."""

    list_display = ('name',)


@admin.register(Recipe)
class MyModelAdmin(admin.ModelAdmin):
    """Регистрация рецепта в админке."""

    list_display = ('name', 'author')
    list_filter = ('tags',)


@admin.register(Ingredient)
class MyModelAdmin(admin.ModelAdmin):
    """Регистрация ингредиента в админке."""

    list_display = ('name', 'measurement_units')
    list_filter = ('name',)
