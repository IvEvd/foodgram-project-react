"""Сериализаторы для приложения Recipes."""

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404

from drf_base64.fields import Base64ImageField

from rest_framework import serializers


from recipes.models import (
    Ingredient,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    ShoppingCartRecipe,
    Tag
)

from users.serializers import UserSerializer

from utils.constants.constants import (
    SECONDS_IN_MINUTE
)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_units',
        read_only=True
    )
    amount = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        coerce_to_string=False
    )

    def to_representation(self, instance):
        """Ингредиенты рецепта для чтения."""
        data = super().to_representation(instance)
        data['amount'] = data['amount'] .normalize()
        return data

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = RecipeIngredient
        depth = 1


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    amount = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        coerce_to_string=False
    )

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        fields = (
            'id',
            'amount',
            'ingredient'
        )
        model = RecipeIngredient
        depth = 2


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериалайзер рецепта для чтения."""

    author = UserSerializer()
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipeingredient_set'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.SerializerMethodField()

    def get_cooking_time(self, instance):
        """Преобразование объекта timedelta в целое число минут."""
        return round(
            instance.cooking_time.total_seconds() / SECONDS_IN_MINUTE
        )

    def get_is_favorited(self, obj):
        """Получение свойства 'в избранных'."""
        if not self.context['request'].user.is_anonymous:
            user = self.context['request'].user
            return obj.favourite_recipe.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Получение свойства 'в списке покупок'."""
        user = self.context['request'].user
        if not user.is_anonymous:
            return ShoppingCartRecipe.objects.filter(
                recipe=obj,
                shopping_cart__author=user
            ).exists()
        return False

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        model = Recipe
        depth = 2


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(many=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    image = Base64ImageField()
    cooking_time = serializers.DurationField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        model = Recipe
        depth = 1

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        validated_data['author'] = self.context['request'].user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags_data:
            RecipeTag.objects.create(recipe=recipe, tag=tag)
        for ingredient_data in ingredients_data:
            amount = ingredient_data.get('amount')
            ingredient_id = ingredient_data.get('id').id
            recipe_ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            RecipeIngredient.objects.create(
                ingredient=recipe_ingredient,
                recipe=recipe,
                amount=amount
            )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Исправление рецепта."""
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )

        tags_data = validated_data.get('tags')
        if tags_data:
            instance.tags.set(tags_data)

        ingredients_data = validated_data.get('ingredients')
        if ingredients_data:
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                amount = ingredient_data.get('amount')
                ingredient_id = ingredient_data.get('id').id
                recipe_ingredient = get_object_or_404(
                    Ingredient, id=ingredient_id
                )
                RecipeIngredient.objects.create(
                    ingredient=recipe_ingredient,
                    recipe=instance,
                    amount=amount
                )
        instance.save()
        return instance

    def to_representation(self, instance):
        """Возврат рецепта для чтения.

        Необходимо чтобы ответ в момент создания рецепта соответствовал
        спецификации API. После создания рецепта сервер вернет ответ в
        виде всех полей RecipeReadSerializer.
        """
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        return read_serializer.data

    def to_internal_value(self, data):
        """Преобразование числа минут в объект timedelta."""
        cooking_time = data.get('cooking_time')
        if cooking_time:
            data['cooking_time'] = timedelta(minutes=int(cooking_time))
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        fields = '__all__'
        model = Tag
