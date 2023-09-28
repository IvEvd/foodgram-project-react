"""Сериализаторы для api_foodgram."""
from datetime import timedelta

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, EmptyResultSet
from django.forms import ValidationError
from django.shortcuts import get_object_or_404

from drf_base64.fields import Base64ImageField

from rest_framework import serializers


from recipes.models import (
    Favourite,
    Ingredient,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    ShoppingCart,
    ShoppingCartRecipe,
    Tag
)

from users.models import (
    Subscription,
    User
)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        """Мета класс."""

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
        """Мета класс."""

        fields = (
            'id',
            'amount',
            'ingredient'
        )
        model = RecipeIngredient
        depth=3


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        """Мета класс."""

        fields = '__all__'
        model = Tag


class ShoppingCartReadSerializer(serializers.ModelSerializer):
    """Сериализатор для создания файла списка покупок."""

    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.DurationField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        """Мета класс."""

        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = ShoppingCartRecipe


class ShoppingCartWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в список покупок."""

    def validate(self, data):
        """Запрет повторного добавления рецепта в избранное."""
        recipe = data.get('recipe')
        shopping_cart = data.get('shopping_cart')
        if ShoppingCartRecipe.objects.filter(
                shopping_cart=shopping_cart, recipe=recipe
                ).exists():
            raise ValidationError(
                    'Добавить рецепт в избранное можно только один раз')
        return data

    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.DurationField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        """Мета класс."""

        fields = '__all__'
        model = ShoppingCartRecipe


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""

    email = serializers.EmailField(max_length=254, required=True)
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета класс."""

        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User

    def get_is_subscribed(self, obj):
        """Получение свойства 'подписан'."""
        if not self.context['request'].user.is_anonymous:
            return obj.following.filter(user=self.context['request'].user).exists()
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
        """Мета класс."""

        fields = (
            'username',
            'email'
        )
        model = User

    def validate(self, data):
        """Запрещает пользователям присваивать себе имя me."""
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
        amount = data['amount']
        data['amount'] = amount.normalize()
        return data

    class Meta:
        """Мета класс."""

        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = RecipeIngredient


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
        return int(instance.cooking_time.total_seconds() / 60)

    def to_representation(self, instance):
        """Объект для выдачи."""
        return super().to_representation(instance)

    def get_is_favorited(self, obj):
        """Получение свойства 'в избранных'."""
        if not self.context['request'].user.is_anonymous:
            user = self.context['request'].user
            return obj.favourite_recipe.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Получение свойства 'в списке покупок'."""
        if not self.context['request'].user.is_anonymous:
            user = self.context['request'].user
            try:
                shopping_cart = get_object_or_404(ShoppingCart, author=user)
                return obj.shopping_cart.filter(
                    shopping_cart=shopping_cart
                    ).exists()
            finally:
                return False
        return False

    class Meta:
        """Мета класс."""

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
        depth = 1


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
        """Мета класс."""

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
        depth=3

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
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
        """Возврат рецепта для чтения."""
        read_serializer = RecipeReadSerializer(instance, context=self.context)
        return read_serializer.data

    def to_internal_value(self, data):
        """Преобразование числа минут в объект timedelta."""
        cooking_time = data.get('cooking_time')
        if cooking_time:
            data['cooking_time'] = timedelta(minutes=int(cooking_time))
        return super().to_internal_value(data)


class RecipeSubscriptionReadSerializer(serializers.ModelSerializer):
    """Сериалайзер рецепта для выдачи в подписке."""

    cooking_time = serializers.SerializerMethodField()

    def get_cooking_time(self, instance):
        """Преобразование объекта timedelta в целое число минут."""
        return int(instance.cooking_time.total_seconds() / 60)

    class Meta:
        """Мета класс."""

        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe
        depth = 1


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериалайзер создания подписок."""

    def validate(self, data):
        """Запрет повторных подписок и подписок на себя."""
        author = data.get('author')
        user = data.get('user')
        if user == author:
            raise ValidationError(
                    'Нельзя подписаться на самого себя')
        if Subscription.objects.filter(
                user=user,
                author=author
                ).exists():
            raise ValidationError(
                    'Подписаться на пользователя можно только один раз')
        return data

    class Meta:
        """Мета класс."""

        fields = ('author', 'user')
        model = Subscription


class SubscriptionReadSerializer(serializers.ModelSerializer):
    """Сериалайзер чтения подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        """Inint сериалайзера."""
        super().__init__(*args, **kwargs)
        self.user_recipes = None

    def get_recipes(self, obj):
        """Получение рецептов."""
        if not self.user_recipes:
            self.user_recipes = Recipe.objects.filter(author=obj.author)
        recipe_serializer = RecipeSubscriptionReadSerializer(
            self.user_recipes,
            many=True,
            context=self.context
        )
        return recipe_serializer.data

    def get_recipes_count(self, obj):
        """Расчет количества рецептов пользователя."""
        if not self.user_recipes:
            self.user_recipes = Recipe.objects.filter(author=obj.author)
        recipes_count = self.user_recipes.count()
        return recipes_count

    def to_representation(self, obj):
        """Вывод данных в выдачу."""
        user_data = UserSerializer(obj.author, context=self.context).data
        user_data['recipes'] = self.get_recipes(obj)
        user_data['recipes_count'] = self.get_recipes_count(obj)
        return user_data

    class Meta:
        """Мета класс."""
    fields = '__all__'


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

    def validate(self, data):
        """Запрет повторного добавления в избранное."""
        recipe = data.get('recipe')
        user = data.get('user')
        if Favourite.objects.filter(
                user=user, recipe=recipe
                ).exists():
            raise ValidationError(
                    'Добавить рецепт в избранное можно только один раз')
        return data

    class Meta:
        """Мета класс."""

        fields = ('recipe', 'user')
        model = Favourite
