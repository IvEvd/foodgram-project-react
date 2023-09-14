from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription

class CustomUserAdmin(UserAdmin):
    # Определите, какие поля вы хотите отображать в форме создания пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    list_filter = ('username', 'email')
admin.site.register(User, CustomUserAdmin)
admin.site.register(Subscription)

