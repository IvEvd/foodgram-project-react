"""Вьюсеты для Recipes API."""

from django.core.exceptions import PermissionDenied

from django_filters import rest_framework as djangofilters

from rest_framework.response import Response
from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)

from .filters import IngredientFilter

from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)

from recipes.models import (
    Ingredient,
    Recipe,
    Tag
)


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Ингридиенты для API."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
    filter_backends = (djangofilters.DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепт для API."""

    queryset = Recipe.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    def get_queryset(self):
        """Чтение рецептов с фильтрацией.

        Фильтрация по тэгам, нахождению в корзине покупок,
        нахождению в избранных.
        """
        queryset = super().get_queryset()
        is_in_shopping_cart = (
            self.request.query_params.get('is_in_shopping_cart')
        )
        is_favorited = self.request.query_params.get('is_favorited')
        tags = self.request.GET.getlist('tags')

        if is_in_shopping_cart:
            queryset = Recipe.objects.filter(
                shoppingcart__author=self.request.user
            )
        if is_favorited:
            queryset = Recipe.objects.filter(
                favourite_recipe__user=self.request.user
            )
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        return queryset.distinct()

    def get_serializer_class(self):
        """Выбор сериалайзера в зависимости от метода запроса."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Создание рецепта через API."""
        serializer.save(author=self.request.user)
        read_serializer = RecipeReadSerializer(
            serializer.instance,
            context={'request': self.request, }
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk):
        """Исправление рецепта через API."""
        recipe = self.get_object()
        if recipe.author != self.request.user:
            raise PermissionDenied('Изменение чужого контента запрещено!')

        serializer = RecipeWriteSerializer(
            recipe,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeReadSerializer(
            serializer.instance,
            context={'request': self.request, }
        )
        return Response(read_serializer.data)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Тэг для API."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
