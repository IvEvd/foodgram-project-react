# Generated by Django 3.2.9 on 2023-09-13 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20230913_1217'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tag',
            name='color_name',
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(max_length=32),
        ),
    ]
