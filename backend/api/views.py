"""Вьюсеты для Foodgram API."""
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash

from django_filters import rest_framework as djangofilters

from rest_framework import (
    mixins,
    permissions,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from pdf_util.constants import TITLE, PAGEINFO
from .filters import IngredientFilter
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartReadSerializer,
    ShoppingCartWriteSerializer,
    SubscriptionSerializer,
    SubscriptionReadSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer
)
from pdf_util.pdf_create import PdfCreator
from recipes.models import (
    Ingredient,
    Favourite,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShoppingCartRecipe,
    Tag
)
from users.models import (
    Subscription,
    User,
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

        if serializer.is_valid():
            serializer.save()
            read_serializer = RecipeReadSerializer(
                serializer.instance,
                context={'request': self.request, }
            )
            return Response(read_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Список покупок для API."""

    queryset = ShoppingCart.objects.all()

    def get_serializer_class(self):
        """Выбор сериалайзера в зависимости от метода запроса."""
        if self.action in ('list', 'retrieve'):
            return ShoppingCartReadSerializer
        return ShoppingCartWriteSerializer

    def get_queryset(self):
        """Получение подписок через API."""
        user = self.request.user
        return super().get_queryset().filter(user=user)

    def create(self, request, *args, **kwargs):
        """Добавление рецепта в список покупок."""
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_cart, created = (
            ShoppingCart.objects.get_or_create(author=self.request.user)
        )
        if created:
            shopping_cart.save()
        shopping_cart_recipe = ShoppingCartRecipe(
            shopping_cart=shopping_cart,
            recipe=recipe
        )
        serializer = ShoppingCartWriteSerializer(shopping_cart_recipe)
        serializer = ShoppingCartWriteSerializer(data=serializer.data)
        if serializer.is_valid():
            serializer.save()
            read_serializer = ShoppingCartReadSerializer(
                serializer.instance,
                context={'request': self.request, }
            )
            return Response(
                read_serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['DELETE'])
    def delete(self, request, pk=None, *args, **kwargs):
        """Убрать рецепт из списка покупок."""
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_cart = get_object_or_404(
            ShoppingCart,
            author=self.request.user
        )
        shopping_cart_recipe = get_object_or_404(
            ShoppingCartRecipe,
            shopping_cart=shopping_cart,
            recipe=recipe
        )
        self.perform_destroy(shopping_cart_recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartPrintViewSet(APIView):
    """Вьюсет списка покупок."""

    def get_queryset(self, request):
        """Получение списка покупок через API."""
        user = self.request.user

        return super().get_queryset().filter(author=user)

    def get(self, request):
        """Создание pdf списка покупок."""
        cart = ShoppingCart.objects.filter(author=request.user)
        list_to_buy = {}
        shopping_cart_recipes = (
            ShoppingCartRecipe.objects.filter(shopping_cart=cart[0])
        )
        for shopping_cart_recipe in shopping_cart_recipes:
            recipe_id = shopping_cart_recipe.recipe.id
            recipe_ingredients = (
                RecipeIngredient.objects.filter(recipe_id=recipe_id)
            )
            for recipe_ingredient in recipe_ingredients:
                ingredient = recipe_ingredient.ingredient.name
                amount = recipe_ingredient.amount
                measurement_units = (
                    recipe_ingredient.ingredient.measurement_units
                )
                if ingredient in list_to_buy:
                    list_amount = list_to_buy[ingredient][0]
                    list_to_buy[ingredient][0] = list_amount + amount
                else:
                    list_to_buy[ingredient] = [amount, measurement_units]

            list_to_print = []
            for element in list_to_buy:
                amount = list_to_buy[element][0].normalize()
                measurement_units = list_to_buy[element][1]
                list_to_print.append(
                    [element, amount.to_eng_string(),
                     measurement_units
                     ])
        pdf = PdfCreator(
            Title=TITLE,
            pageinfo=PAGEINFO,
            data=[]
        )
        empty_list_to_print = [[None] * 3]
        if list_to_print:
            return pdf.create_pdf_with_table(list_to_print)
        else:
            return pdf.create_pdf_with_table(empty_list_to_print)


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


class SubscriptionsViewSet(viewsets.ModelViewSet):
    """Вьюсет подписок."""

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionReadSerializer

    def create(self, request, *args, **kwargs):
        """Подписаться."""
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)

        subscription = Subscription(user=request.user, author=author)
        serializer = SubscriptionSerializer(subscription)
        serializer = SubscriptionSerializer(data=serializer.data)
        if serializer.is_valid():
            serializer.save()
            read_serializer = SubscriptionReadSerializer(
                serializer.instance,
                context={'request': self.request, }
            )
            return Response(
                read_serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            print(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['DELETE'])
    def delete(self, request, pk=None, *args, **kwargs):
        """Отписаться."""
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)
        subscription = get_object_or_404(
            Subscription,
            user=request.user,
            author=author)
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Получение подписок через API."""
        user = self.request.user
        return super().get_queryset().filter(user=user)


class FavouriteViewSet(viewsets.ModelViewSet):
    """Вьюсет избранных."""

    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer

    def create(self, request, *args, **kwargs):
        """Добавить рецепт в избранные."""
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)

        favourite = Favourite(user=request.user, recipe=recipe)
        serializer = FavouriteSerializer(favourite)
        serializer = FavouriteSerializer(data=serializer.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['DELETE'])
    def delete(self, request, pk=None, *args, **kwargs):
        """Убрать рецепт из избранных."""
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favourite = get_object_or_404(
            Favourite,
            user=request.user,
            recipe=recipe
        )
        self.perform_destroy(favourite)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Получение подписок через API."""
        user = self.request.user
        return super().get_queryset().filter(user=user)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Создание пользователя."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data['password'])
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me',
        url_name='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_me_data(self, request):
        """Позволяет пользователю получить информацию о себе.

        С возможностью редактировать её.
        """
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data,
                partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post', ],
        url_path='set_password',
        url_name='set_password',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def change_password(self, request):
        """Смена пароля."""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(
                {'error': 'Текущий пароль введен неверно'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        return Response(
            {'message': 'Пароль успешно изменен'},
            status=status.HTTP_200_OK
        )
