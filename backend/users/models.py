"""Модели пользователей."""
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Кастомная модель User."""

    USER = "user"
    ADMIN = 'admin'

    roles = [
        (USER, USER),
        (ADMIN, ADMIN),
    ]
    role = models.CharField(
        'Статус пользователя',
        max_length=9,
        choices=roles,
        default=USER
    )
    confirmation_code = models.CharField(
        verbose_name='токен пользователя',
        max_length=100,
        blank=True,
        null=True,
    )

    class Meta:
        """Мета класс."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        """Название объекта."""
        return self.username

    @property
    def is_subscribed(self):
        """Свойство 'подписан на автора'."""
        return self.follower.filter(author=self.profile_user).exists()


class Subscription(models.Model):
    """Подписка."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Отслеживаемый',
        )
    created = models.DateTimeField('Дата комментария', auto_now_add=True)

    def clean(self):
        """Запрет подписки на себя."""
        super().clean()
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя!')

    class Meta:
        """Мета класс."""

        ordering = ['-created']
        verbose_name = 'Подпискa'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription',
                )]
