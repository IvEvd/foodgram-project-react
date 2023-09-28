"""Маршрутизация для API Foodgram."""

from django.urls import include, path

from rest_framework import routers

from .views import (
    FavouriteViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    ShoppingCartPrintViewSet,
    TagViewSet,
    UserViewSet,
    SubscriptionsViewSet,
)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite', FavouriteViewSet)
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet
)

router.register(r'tags', TagViewSet)
router.register(r'users/subscriptions', SubscriptionsViewSet)
router.register(r'users/(?P<user_id>\d+)/subscribe', SubscriptionsViewSet)
router.register(r'users', UserViewSet)


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
    path('recipes/download_shopping_cart/',
         ShoppingCartPrintViewSet.as_view()
         ),
    path('', include(router.urls)),
]
