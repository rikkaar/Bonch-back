import requests
from bs4 import BeautifulSoup as Soup
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from registration.models import Faculties, Groups


class Parse:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15',
            'Accept-Language': 'ru',
        }

    def groups(self):
        groups_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
        html = self.session.get(groups_url).text
        soup = Soup(html, 'lxml')
        for faculty in soup.find_all(class_='vt252'):
            try:
                Faculties(
                    faculty_name=faculty.find(class_='vt253').text.strip()
                ).save()
            except IntegrityError:
                pass
            # fk = Faculties.objects.get(faculty_name=faculty.find(class_='vt253').text.strip()).pk
            for group in faculty.find_all(class_='vt256'):
                Groups(
                    group_name=group.get('data-nm'),
                    group_faculty=Faculties.objects.get(faculty_name=faculty.find(class_='vt253').text.strip()),
                    group_link=group.get('href'),
                ).save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        Parse().groups()


""" 
    Какие нужны функции?
    Пока остановимся на двух моделях:
    >> Парсинг всех групп. Одноразовая операция
    > Получить суп (в этом случае всего один раз) - для этого есть
    библиотека. нет смысла строить велосипед
    >
    >
    >> Парсинг расписания у всех групп по порядку
    >
    > 
    > 
    
"""
