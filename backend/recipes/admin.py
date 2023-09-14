from django.contrib import admin
from django import forms
from webcolors import CSS3_HEX_TO_NAMES
from .models import Ingredient, Recipe,ShoppingList, Tag


admin.site.register(ShoppingList)


@admin.register(Tag)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    
@admin.register(Recipe)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('tags',)

@admin.register(Ingredient)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_units')
    list_filter = ('name',)