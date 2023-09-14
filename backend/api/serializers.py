"""Сериализаторы для api_foodgram."""
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
import webcolors
import io

from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers
from drf_base64.fields import Base64ImageField

from recipes.models import(
    Recipe,
    Ingredient,
    ShoppingList,
    Tag,
)

from users.models import( 
    User,
    Subscription
)




class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        fields = '__all__'
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        fields = '__all__'
        model = ShoppingList


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User"""
    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed')
        model = User
    
    def get_is_subscribed(self, obj):
        # Проверяем, подписан ли текущий пользователь на пользователя obj
        if not self.context['request'].user.is_anonymous:
            return obj.follower.filter(author=self.context['request'].user).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объекта класса User."""

    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email'
        )

    def validate(self, data):
        """Запрещает пользователям присваивать себе имя me
        и использовать повторные username и email.
        """
        if data.get('username') == 'me':
            raise serializers.ValidationError(
                'Использовать имя me запрещено'
            )
        return data


class UserRecieveTokenSerializer(serializers.Serializer):
    """Сериализатор для объекта класса User при получении токена JWT."""

    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=150,
        required=True
    )

class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    image = serializers.ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time',)
        model = Recipe

class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    #author = UserSerializer()
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    '''author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )'''
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time',)
        model = Recipe

class SubscriptionSerializer(serializers.ModelSerializer):


    class Meta:
        model = Subscription
        fields = ('user', 'author', 'created')

        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author']
            ),
        ]
    
    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        
        # Проверяем, не существует ли уже объекта Subscription с такой комбинацией user и author
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Уже существует подписка с такой комбинацией user и author")
        
        return data
    
    '''def validate(self, data):
        author = self.context.get('user_id')
        request = self.context.get('request')
        if request.user == author:
            raise ValidationError(
                    'Нельзя подписаться на самого себя')
        if request.method == 'POST':
            if Subscription.objects.filter(
                    user=request.user,
                    author= data.get('author')).exists():
                raise ValidationError(
                    'Подписаться на пользователя можно только один раз')
        return data'''

    # author = UserSerializer()'''
    '''def validate(self, data):
        author = self.context.get('user_id')
        request = self.context.get('request')
        if request.user == author:
            raise ValidationError(
                    'Нельзя подписаться на самого себя')
        if request.method == 'POST':
            if Subscription.objects.filter(
                    user=request.user,
                    author= data.get('author')).exists():
                raise ValidationError(
                    'Подписаться на пользователя можно только один раз')
        return data'''

    class Meta:
        """Мета класс."""

        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=['user', 'author']
            ),
        ]

        fields = '__all__'
        model = Subscription
