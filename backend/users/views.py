"""Вьюсеты для Users API."""

from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash

from rest_framework import (
    permissions,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.constants.constants import (
    TITLE,
    PAGEINFO
)

from .serializers import (
    FavouriteSerializer,
    ShoppingCartReadSerializer,
    ShoppingCartWriteSerializer,
    SubscriptionSerializer,
    SubscriptionReadSerializer,
    UserCreateSerializer,
    UserSerializer
)
from utils.pdf_util.pdf_create import PdfCreator
from recipes.models import (
    Favourite,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShoppingCartRecipe,
)
from users.models import (
    Subscription,
    User,
)


class FavouriteViewSet(viewsets.ModelViewSet):
    """Вьюсет избранных рецептов."""

    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer

    def create(self, request, *args, **kwargs):
        """Добавить рецепт в избранное."""
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = FavouriteSerializer(
            data={
                'recipe': recipe.id,
                'user': request.user.id
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
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
        serializer = ShoppingCartWriteSerializer(
            data={
                'shopping_cart': shopping_cart.id,
                'recipe': recipe.id
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = ShoppingCartReadSerializer(
            serializer.instance,
            context={'request': self.request, }
        )
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
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


class SubscriptionsViewSet(viewsets.ModelViewSet):
    """Вьюсет подписок."""

    queryset = Subscription.objects.all()
    serializer_class = SubscriptionReadSerializer

    def create(self, request, *args, **kwargs):
        """Подписаться."""
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)
        serializer = SubscriptionSerializer(
            data={
                'user': request.user.id,
                'author': author.id
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = SubscriptionReadSerializer(
            serializer.instance,
            context={'request': self.request, }
        )
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED
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


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Создание пользователя."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.set_password(request.data['password'])
        user.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
