"""Загрузка CSV в базу данных."""
import os
import csv

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone

from foodgram_backend.settings import BASE_DIR
from recipes.models import Ingredient
from users.models import User

data_folder = os.path.join(BASE_DIR, 'data/')
ingredients_file = 'ingredients.csv'
file_name_dict = {
    'ingredients.csv': Ingredient,
}


class Command(BaseCommand):
    """Загрузка CSV в базу данных."""

    help = 'Import data from CSV files'

    def import_norelatedfield_models(self, *args, **options):
        """
        Загрузка моделей без связанных полей.
    
        При загрузке цифр преобразовывает их в int
        """
        for file_name in file_name_dict:
            file_path = os.path.join(data_folder, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                obj = file_name_dict[file_name]
                obj_count = 0
                for row in csv_reader:
                    for key, value in row.items():
                        if value.isdigit():
                            row[key] = int(value)
                    obj.objects.get_or_create(**row)
                    obj_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"Количество созданных записей {file_name}: {obj_count} "
            ))

    

    def handle(self, *args, **options):
        """Главная функция."""
        self.import_norelatedfield_models(self, *args, **options)

