from django.shortcuts import render, get_object_or_404
from rest_framework import (
    filters,
    mixins,
    permissions,
    status,
    viewsets,
)
from rest_framework.response import Response
from users.models import User
from recipes.models import(
    Ingredient,
    Recipe,
    ShoppingList,
    Tag
)

from .serializers import (
    
    IngredientSerializer,
    RecipeSerializer,
    ShoppingListSerializer,
    TagSerializer,
    UserSerializer
)
from rest_framework.decorators import action

class IngredientViewSet(viewsets.ModelViewSet):
    """Ингридиенты для API."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепт для API."""
    
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer


class ShoppingListViewSet(viewsets.ModelViewSet):
    """Список покупок для API."""
    
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer


class TagViewSet(viewsets.ModelViewSet):
    """Тэг для API."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """Вьюсет для обьектов модели User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    @action(
        detail=False,
        methods=['get', 'patch', 'delete'],
        url_path=r'(?P<id>[\w.@+-]+)',
        url_name='get_user'
    )
    def get_user_by_username(self, request, id):
        """
        Обеспечивает получание данных пользователя по его username и
        управление ими.
        """
        user = get_object_or_404(User, id=id)
        if request.method == 'PATCH':
            serializer = UserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        url_name='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    
    def get_me_data(self, request):
        """
        Позволяет пользователю получить подробную информацию о себе
        и редактировать её.
        """
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)