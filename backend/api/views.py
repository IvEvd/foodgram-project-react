from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import (
    filters,
    mixins,
    permissions,
    status,
    viewsets,
)
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from users.models import(
    User,
    Subscription
) 
from recipes.models import(
    Favourite,
    Ingredient,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    ShoppingCart,
    Tag
)
from django.contrib.auth import update_session_auth_hash
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserRecieveTokenSerializer,
    UserSerializer

)
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin
)

from .utils import send_confirmation_code
from .permissions import IsAdminSelf, IsAdminOrReadOnly
from rest_framework.decorators import action

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


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепт для API."""
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        """Выбор сериалайзера в зависимости от метода запроса."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        print(serializer.instance)
        read_serializer = RecipeReadSerializer(serializer.instance, context={'request': self.request,})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
    
    
    '''def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )
        created_object = serializer.instance

        # Создайте URL для объекта, используя reverse
        created_object_url = reverse('api:recipe-detail', args=[created_object.id])

        # Верните перенаправление на созданный объект
        return Response({'url': created_object_url}, status=status.HTTP_201_CREATED)'''


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Список покупок для API."""
    
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer


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
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    

    def create(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)

        subscription = Subscription(user=request.user, author=author)
        serializer = SubscriptionSerializer(subscription)
        serializer = SubscriptionSerializer(data=serializer.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['DELETE'])
    def delete(self, request, pk=None, *args, **kwargs):
        user_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=user_id)
        subscription = get_object_or_404(Subscription, user=request.user, author=author)
        self.perform_destroy(subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_queryset(self):
        """Получение подписок через API."""
        user = self.request.user
        return super().get_queryset().filter(user=user)
    


class FavouriteViewSet(viewsets.ModelViewSet):
    queryset = Favourite.objects.all()
    serializer_class = FavouriteSerializer
    

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)

        favourite = Favourite(user=request.user, recipe=recipe)
        serializer = FavouriteSerializer(favourite)
        serializer = FavouriteSerializer(data=serializer.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['DELETE'])
    def delete(self, request, pk=None, *args, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favourite = get_object_or_404(Favourite, user=request.user, recipe=recipe)
        self.perform_destroy(favourite)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_queryset(self):
        """Получение подписок через API."""
        user = self.request.user
        return super().get_queryset().filter(user=user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(
        detail=False,
        methods=['post',],
        url_path='set_password',
        url_name='set_password',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def change_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
    
        if not user.check_password(current_password):
            return Response({'error': 'Текущий пароль введен неверно'}, status=status.HTTP_400_BAD_REQUEST)
    
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
    
        return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)



'''class UserViewSet(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    """Вьюсет для обьектов модели User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
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


class UserCreateViewSet(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    """Вьюсет для создания обьектов класса User."""

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request):
        """Создает объект класса User.
        Отправляет на почту пользователя код подтверждения.
        """
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get_or_create(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
            )[settings.CREATE_USER_INDEX]
        except IntegrityError:
            return Response(
                'Имя пользователя или электронная почта занята.',
                status=status.HTTP_400_BAD_REQUEST
            )
        confirmation_code = default_token_generator.make_token(user)
        send_confirmation_code(
            email=user.email,
            confirmation_code=confirmation_code
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserReceiveTokenViewSet(mixins.CreateModelMixin,
                              viewsets.GenericViewSet):
    """Вьюсет для получения пользователем JWT токена."""

    queryset = User.objects.all()
    serializer_class = UserRecieveTokenSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Предоставляет пользователю JWT токен по коду подтверждения."""
        serializer = UserRecieveTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get('username')
        confirmation_code = serializer.validated_data.get('confirmation_code')
        user = get_object_or_404(User, username=username)

        if not default_token_generator.check_token(user, confirmation_code):
            message = {'confirmation_code': 'Код подтверждения невалиден'}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)
        message = {'token': str(AccessToken.for_user(user))}
        return Response(message, status=status.HTTP_200_OK)'''