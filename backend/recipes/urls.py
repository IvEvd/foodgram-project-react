"""Маршрутизация приложения recipes."""

from django.urls import include, path

from rest_framework import routers

from recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)

app_name = 'recipes'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
