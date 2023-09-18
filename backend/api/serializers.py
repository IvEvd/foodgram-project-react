"""Сериализаторы для api_foodgram."""
from decimal import Decimal
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
import webcolors
import io

from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers
from drf_base64.fields import Base64ImageField

from recipes.models import(
    Favourite,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    Ingredient,
    ShoppingCart,
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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    amount = serializers.DecimalField(
        max_digits=7,  # Максимальное количество цифр в числе
        decimal_places=3,  # Максимальное количество знаков после запятой
        coerce_to_string=False
    )
    
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
   
    class Meta:
        fields = ('id', 'amount', 'ingredient')
        model = RecipeIngredient
        depth=3


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        fields = '__all__'
        model = ShoppingCart


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


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""
    
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(source='ingredient.measurement_units', read_only=True)
    amount = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        coerce_to_string=False
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        amount = data['amount']
        data['amount'] = amount.normalize()
        return data
    
    
    
    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = RecipeIngredient


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    tags = TagSerializer(read_only=True, many=True)
    image = serializers.ImageField()
    ingredients = RecipeIngredientReadSerializer(many=True, source='recipeingredient_set')
    is_favorited = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if not self.context['request'].user.is_anonymous:
            return obj.favourite_recipe.filter(user=user).exists()
        return False
    
    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'name', 'image', 'text', 'cooking_time',)
        model = Recipe
        depth = 1

class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    ingredients = RecipeIngredientSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    image = Base64ImageField()

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time',)
        model = Recipe
        depth=3
    
    def create(self, validated_data):
        
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags_data:
            RecipeTag.objects.create(recipe=recipe, tag=tag)
        for ingredient_data in ingredients_data:
            amount = ingredient_data.get('amount')
            ingredient_id = ingredient_data.get('id').id
            recipe_ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            print(recipe_ingredient)
            RecipeIngredient.objects.create(
            ingredient=recipe_ingredient, recipe=recipe, amount=amount) 
        return recipe
    
    def to_representation(self, instance):
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        return read_serializer.data

    


class SubscriptionSerializer(serializers.ModelSerializer):

    def validate(self, data):
        author = data.get('author')
        user = data.get('user')
        request = self.context.get('request')
        if user == author:
            raise ValidationError(
                    'Нельзя подписаться на самого себя')
        if Subscription.objects.filter(
                user=user,
                author= author).exists():
            raise ValidationError(
                    'Подписаться на пользователя можно только один раз')
        return data
    
    class Meta:
        """Мета класс."""

        fields = ('author', 'user')
        model = Subscription
    

class FavouriteSerializer(serializers.ModelSerializer):

    def validate(self, data):
        recipe = data.get('recipe_id')
        user = data.get('user')
        request = self.context.get('request')
        if Favourite.objects.filter(
                user=user
            ).exists():
            raise ValidationError(
                    'Добавить рецепт в избранное можно только один раз')
        return data
    
    class Meta:
        """Мета класс."""

        fields = ('recipe', 'user')
        model = Favourite
    # author = UserSerializer()'''
