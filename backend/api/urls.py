"""Маршрутизация для API Yatube."""
from django.contrib import admin
from django.urls import include, path

from rest_framework import routers

from .views import (
    FavouriteViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ShoppingCartViewSet,
    TagViewSet,
    UserViewSet,
    SubscriptionsViewSet
    
)
'''UserCreateViewSet,
    UserReceiveTokenViewSet'''

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'recipes/(?P<recipe_id>\d+)/favorite', FavouriteViewSet)
router.register(r'tags', TagViewSet)
router.register(r'users/subscriptions', SubscriptionsViewSet)
router.register(r'users/(?P<user_id>\d+)/subscribe', SubscriptionsViewSet)
router.register(r'users', UserViewSet)


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
    
]

'''path(
        'users/signup/',
        UserCreateViewSet.as_view({'post': 'create'})
    ),
    path(
        'auth/token/',
        UserReceiveTokenViewSet.as_view({'post': 'create'})
    )'''