"""Модели приложения рецепты."""
from django.db import models

from colorfield.fields import ColorField

from users.models import User


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField('Название рецепта', max_length=256, unique=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.SET_DEFAULT,
        related_name='recipe_author',
        default=1,
    )
    image = models.ImageField(
        'Изображение блюда',
        upload_to='recipes/images/',
        null=True,
        blank=True,
        default=None
    )
    text = models.TextField('Инструкции по приготовлению')
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name='Ингредиент',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        related_name='recipe_ingredients'
    )
    cooking_time = models.DurationField('Время готовки')

    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Тэг',
        through='RecipeTag',
        through_fields=('recipe', 'tag'))

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name',)

    @property
    def is_favorited(self):
        """Рецепт в списке избранных."""
        return self.favourite_recipe.filter(
            recipe_liker=self.profile_user
        ).exists()

    @property
    def is_in_shopping_cart(self):
        """Рецепт в списке покупок."""
        shopping_cart = ShoppingCart.objects.get(author=self.profile_user)
        return self.shopping_cart_recipe.filter(
            shopping_cart=shopping_cart
        ).exists()

    def __str__(self):
        """Название объекта класса."""
        return self.name


class ShoppingCart(models.Model):
    """Список покупок."""

    author = models.OneToOneField(
        User,
        verbose_name='Автор списка покупок',
        on_delete=models.CASCADE,
        related_name='user_shopping_cart'
    )
    recipe = models.ManyToManyField(
        'Recipe',
        verbose_name='рецепты',
        through='ShoppingCartRecipe',
        through_fields=('shopping_cart', 'recipe'))

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('id',)


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField('Название ингредиента', max_length=100)
    measurement_units = models.CharField('Единицы измерения', max_length=100)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)


class Tag(models.Model):
    """Модель тэга."""

    name = models.CharField('Название тэга', max_length=50, unique=True)
    color = ColorField(default='#FF0000')
    slug = models.SlugField('Слаг тэга', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        """Название объекта класса."""
        return self.slug


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента.

    Содержит количество ингредиента для рецепта.
    """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField(
        'Количество ингредиента',
        max_digits=7,
        decimal_places=3,
        default=0
    )


class RecipeTag(models.Model):
    """Модель связи рецепта и тэга."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class ShoppingCartRecipe(models.Model):
    """Список покупок."""

    shopping_cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        blank=True,
        related_name='shopping_cart'
    )


class Favourite(models.Model):
    """Избранные рецепты."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_liker',
        verbose_name='Добавил в избранное',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favourite_recipe'
    )
    created = models.DateTimeField('Дата комментария', auto_now_add=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite',
            )]
