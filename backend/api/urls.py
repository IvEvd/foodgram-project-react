"""Маршрутизация для API Yatube."""
from django.contrib import admin
from django.urls import include, path

from rest_framework import routers

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    ShoppingListViewSet,
    TagViewSet,
    UserViewSet,
)

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'users', UserViewSet)

'''router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    viewset=ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    viewset=CommentViewSet,
    basename='comments'
)'''

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]

'''path(
        'auth/signup/',
        UserCreateViewSet.as_view({'post': 'create'})
    ),
    path(
        'auth/token/',
        UserReceiveTokenViewSet.as_view({'post': 'create'})
    ),'''