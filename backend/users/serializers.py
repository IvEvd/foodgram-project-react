"""Сериализаторы для приложения Users."""

from django.forms import ValidationError

from rest_framework import serializers

from recipes.models import (
    Favourite,
    Recipe,
    ShoppingCartRecipe,
)
from users.models import (
    Subscription,
    User
)


class FavouriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""

    def to_representation(self, obj):
        """Вывод данных в выдачу."""
        recipe = obj.recipe
        read_serializer = RecipeSubscriptionReadSerializer(recipe).data
        return read_serializer

    def validate(self, data):
        """Запрет повторного добавления в избранное."""
        recipe = data.get('recipe')
        user = data.get('user')
        if Favourite.objects.filter(
                user=user, recipe=recipe
        ).exists():
            raise ValidationError(
                'Добавить рецепт в избранное можно только один раз'
            )
        return data

    class Meta:
        """Мета класс."""

        fields = ('recipe', 'user')
        model = Favourite


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
        """Запрет повторного добавления рецепта в список покупок."""
        recipe = data.get('recipe')
        shopping_cart = data.get('shopping_cart')
        if ShoppingCartRecipe.objects.filter(
                shopping_cart=shopping_cart, recipe=recipe
        ).exists():
            raise ValidationError(
                'Добавить рецепт в список покупок можно только один раз'
            )
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
    password = serializers.CharField(write_only=True, required=True)
    username = serializers.RegexField(
        regex=r'^[\w.@+-]+$',
        max_length=150,
        required=True
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Мета класс."""

        fields = (
            'email',
            'password',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User

    def validate(self, data):
        """Запрещает пользователям присваивать себе имя me."""
        username = data.get('username')
        email = data.get('email')
        if username == 'me':
            raise serializers.ValidationError(
                'Использовать имя me запрещено'
            )
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Нельзя использовать email повторно'
            )
        return data

    def get_is_subscribed(self, obj):
        """Получение свойства 'подписан'."""
        if not self.context['request'].user.is_anonymous:
            return obj.following.filter(
                user=self.context['request'].user
            ).exists()
        return False


class UserCreateSerializer(UserSerializer):
    """Сериализатор создания пользователя."""

    class Meta(UserSerializer.Meta):
        """Мета класс."""

        fields = (
            'email',
            'password',
            'id',
            'username',
            'first_name',
            'last_name'
        )


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
                'Нельзя подписаться на самого себя'
            )
        if Subscription.objects.filter(
                user=user,
                author=author
        ).exists():
            raise ValidationError(
                'Подписаться на пользователя можно только один раз'
            )
        return data

    class Meta:
        """Мета класс."""

        fields = ('author', 'user')
        model = Subscription


class SubscriptionReadSerializer(serializers.ModelSerializer):
    """Сериалайзер чтения подписок."""

    class Meta:
        """Мета класс."""
    fields = '__all__'
    model = User


class SubscriptionReadSerializer(serializers.ModelSerializer):
    """Сериалайзер чтения подписок."""

    def to_representation(self, obj):
        """Вывод данных в выдачу."""
        author = obj.author
        user_data = UserSerializer(author, context=self.context).data
        user_data['recipes'] = RecipeSubscriptionReadSerializer(
            author.recipe_author,
            many=True,
            context=self.context
        ).data
        user_data['recipes_count'] = (
            Recipe.objects.filter(author=author).count()
        )
        return user_data

    class Meta:
        """Мета класс."""
    fields = '__all__'
    model = User
