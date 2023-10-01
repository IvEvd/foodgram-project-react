"""Маршрутизация приложения users."""

from django.urls import include, path

from rest_framework import routers

from users.views import (
    FavouriteViewSet,
    ShoppingCartViewSet,
    ShoppingCartPrintViewSet,
    SubscriptionsViewSet,
    UserViewSet
)
app_name = 'users'

router = routers.DefaultRouter()
router.register(r'recipes/(?P<recipe_id>\d+)/favorite', FavouriteViewSet)
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet
)
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
