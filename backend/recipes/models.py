from django.db import models
from django.contrib.auth import get_user_model
from users.models import User


class Recipe(models.Model):
    """Модель рецепта"""

    name = models.CharField('Название рецепта', max_length=256)
    author = models.ForeignKey(User, verbose_name='Автор рецепта', on_delete=models.CASCADE)
    image = models.ImageField(
        'Изображение блюда',
        upload_to='recipes/images/',
        null=True,
        blank=True,
        default=None
    )
    text = models.TextField('Инструкции по приготовлению')
    ingredient = models.ManyToManyField(
        'Ingredient',
        verbose_name='Ингредиент',
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient')
    )
    cooking_time = models.DurationField('Время готовки')
    tag = models.ManyToManyField(
        'Tag',
        verbose_name='Тэг',
        through='RecipeTag',
        through_fields=('recipe', 'tag'))
    
    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('name',)

class ShoppingList(models.Model):
    author = models.OneToOneField(User, verbose_name='Автор списка покупок', on_delete=models.CASCADE)
    name = models.CharField(
        'Название списка покупок',
        max_length=256,
        default='Список покупок'
    )
    recipe = models.ManyToManyField(
        'Recipe',
        verbose_name='рецепты',
        through='ShoppingListRecipe',
        through_fields=('shopping_list', 'recipe'))
    
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('id',)

class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField('Название ингредиента', max_length=256)
    amount = models.DecimalField('Количество ингредиента', max_digits=7, decimal_places=3)
    measurement_units = models.CharField('Единицы измерения', max_length=256)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

class Tag(models.Model):
    """Модель тэга"""
    name = models.CharField('Название тэга', max_length=256, unique=True)
    slug = models.SlugField('Слаг тэга', max_length=50, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)

class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

class ShoppingListRecipe(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)