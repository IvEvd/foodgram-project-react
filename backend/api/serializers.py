"""Сериализаторы для api_yatube."""
from django.forms import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from recipes.models import(
    Recipe,
    Ingredient,
    ShoppingList,
    Tag,
)

from users.models import User


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    class Meta:
        fields = '__all__'
        model = Recipe


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        fields = '__all__'
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        fields = ('name', 'slug')
        model = Tag


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        fields = '__all__'
        model = ShoppingList


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User"""

    class Meta:
        fields = '__all__'
        model = User