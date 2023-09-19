from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from users.models import User
from webcolors import CSS3_HEX_TO_NAMES, name_to_hex
from colorfield.fields import ColorField


class Recipe(models.Model):
    """Модель рецепта"""

    name = models.CharField('Название рецепта', max_length=256)
    author = models.ForeignKey(User, verbose_name='Автор рецепта', on_delete=models.CASCADE, related_name='recipe_author')
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
        return self.favourite_recipe.filter(recipe_liker=self.profile_user).exists()
    
    @property
    def is_in_shopping_cart(self):
        shopping_cart = ShoppingCart.objects.get(author=self.profile_user)
        return self.shopping_cart_recipe.filter(shopping_cart=shopping_cart).exists()
    
    def __str__(self):
        return self.name

class ShoppingCart(models.Model):
    author = models.OneToOneField(User, verbose_name='Автор списка покупок', on_delete=models.CASCADE)
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
    """Модель ингредиента"""
    name = models.CharField('Название ингредиента', max_length=100)
    measurement_units = models.CharField('Единицы измерения', max_length=100)
    

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

        
        '''constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite',
                )]'''

class Tag(models.Model):
    """Модель тэга"""
    name = models.CharField('Название тэга', max_length=256, unique=True)
    slug = models.SlugField('Слаг тэга', max_length=50, unique=True)
    color = ColorField(default='#FF0000')

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField('Количество ингредиента', max_digits=7, decimal_places=3, default=0)

class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

class ShoppingCartRecipe(models.Model):
    shopping_cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, blank=True, related_name='shopping_cart')

class Favourite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_liker',
        verbose_name='Добавил в избранное',
    )
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favourite_recipe')
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