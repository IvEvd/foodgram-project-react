# Generated by Django 3.2.9 on 2023-09-18 14:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0014_auto_20230918_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shoppingcartrecipe',
            name='shopping_cart',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.shoppingcart'),
        ),
    ]
