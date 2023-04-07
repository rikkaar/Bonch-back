import time
import os
import requests
import datetime
from bs4 import BeautifulSoup as Soup
from django.core.management.base import BaseCommand
from django.db import IntegrityError
import asyncio
import aiohttp
import logging

from server.models import Faculties, Groups, Classes

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

logging.basicConfig(level=logging.DEBUG, filename='parser_log.log', filemode='w', format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()

class Parse:
    def __init__(self):
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15',
            'Accept-Language': 'ru',
        }

    async def get_page_data(self, session, link, group, start_parse):
        general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
        headers = {
            'User-Agent': 'Chrome/107.0.0.0 Safari/537.36',
            'Accept-Language': 'ru',
        }

        async with session.get(url=link, headers=headers) as response:
            response_text = await response.text()   # получаем сухой html-код
            html = Soup(response_text, 'lxml').find(class_='vt244b').contents    # СТАБИЛЬНО. ищем блок с расписанием, и обращаемся к его потомкам. Если их нет, то html = []
            for week in html: # если есть хотя бы одна пара, то цикл запустится, если поле пустое, то ничего не произойдет
                time = week.find(class_='vt283').parent.text  # СТАБИЛЬНО. получения тега, содержащего время. Далее разбиваем на два объекта date с началом и концом пары
                end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
                start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
                for day in week.find_all(class_='vt258'):   # СТАБИЛЬНО.
                    try:
                        date_offset = int(day.parent.get('class')[-1][-1]) - 1  # СТАБИЛЬНО. ['vt239', 'rasp-day', 'rasp-day1'] это особенность bs4.
                        datepush = start_parse + datetime.timedelta(days=date_offset)  # дата понедельника + номер текущего дня
                        name = day.find(class_="vt240").text.strip()    # +-СТАБИЛЬНО.
                        type = day.find(class_="vt243").text.strip()    # +-СТАБИЛЬНО - выбирается из списка. Врядли можно не выбрать, хотя....
                        try:
                            teachers = day.find(class_="teacher").text.strip().split(' ')   # НЕСТАБИЛЬНО.
                            teachers = (lambda a, n=2: [' '.join(a[i:i + n]) for i in range(0, len(a), n)])(teachers)  # превращаем в массив учителей
                        except AttributeError:
                            teachers = []
                            if name != 'Военная подготовка' and name != 'Строевая подготовка':
                                logging.info(f'{group.group_name, str(datepush)} ERROR, got []:{link}')
                        # place = day.find(class_="vt242").text.strip()  # НЕСТАБИЛЬНО.
                        # place = place.split(':')[1].strip().split(';')
                        # aud = place[0]
                        # building = None
                        # if (len(place) == 2):
                        #     if '/' in place[1]:
                        #         building = place[1][-1]
                        #     else:
                        #         building = 'k'
                        try:
                            building = None
                            place = day.find(class_="vt242").text.strip()   # НЕСТАБИЛЬНО.
                            place = place.split(':')[1].strip().split(';')
                            aud = place[0]
                            if len(place) != 1:
                                try:
                                    building = place[1]
                                except IndexError:
                                    logging.info(f'{group.group_name, str(datepush)} NO BUILDING:{link}')
                        except (AttributeError, IndexError) as error:
                            if week.find(class_='vt283').text == 'ФЗ':
                                aud = 'Спортивные площадки'
                                building = None
                                if name != 'Элективные дисциплины по физической культуре и спорту' and name != 'Физическая культура и спорт':
                                    logging.info(f'{group.group_name, str(datepush)} GOT FZ:{link}')
                            else:
                                aud = None
                                building = None
                                if name != 'Военная подготовка' and name != 'Строевая подготовка':
                                    logging.info(f'{group.group_name, str(datepush)} ERROR, not FZ:{link}')
                        try:
                            Classes(
                                class_name=name,
                                class_audience=aud,
                                class_building=building,
                                class_type=type,
                                class_date=datepush,
                                class_start=start,
                                class_end=end,
                                class_teachers=teachers,
                                group_id=group,
                            ).save()
                        except UnboundLocalError:
                            logging.exception('DataError')
                            logging.info(f'{group.group_name, str(datepush), day}')
                            pass
                        # except AttributeError:
                        #     pass
                    except AttributeError:
                        print(datepush, group.group_name)
                        logging.exception('AttributeError')
                        logging.info(f'{group.group_name, str(datepush), day}')

            # group.end_parse += datetime.timedelta(days=7)
            # group.save(update_fields=["end_parse"])
            # Groups.objects.get(group).update(end_parse=F("end_parse") + datetime.timedelta(days=7))

    async def gather_data(self, pfrom, pto):
        async with aiohttp.ClientSession() as session:
            tasks = []
            general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
            credit_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zachetov-studentov-ochnoy-i-vecherney-form-obucheniya'
            for i in range(pfrom, pto):
                group = Groups.objects.get(pk=i)
                end_parse = datetime.datetime(2023, 4, 7)
                start_parse = datetime.datetime.fromisocalendar(2023, datetime.datetime(2023, 4, 1).isocalendar().week, 1)
                while end_parse >= start_parse:
                    url = general_url + group.group_link + '&date=' + str(start_parse)
                    # html = Soup(group_url, 'lxml').find(class_='vt244b').contents
                    task = asyncio.create_task(self.get_page_data(session, url, group, start_parse))
                    tasks.append(task)
                    start_parse += datetime.timedelta(days=7)
            # for i in range(1, 5):
            #     general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
            #     group = Groups.objects.get(pk=i)
            #     url = general_url + group.group_link + '&date=' + str(group.end_parse)
            #     # html = Soup(group_url, 'lxml').find(class_='vt244b').contents
            #     task = asyncio.create_task(self.get_page_data(session, url, group))
            #     tasks.append(task)
            await asyncio.gather(*tasks)

    def main(self):
        # a = [1, 41, 81, 121, 161, 201, 241, 281, 321, 361, 401, 441, 447]
        # a = [1, 51, 101, 151, 201, 251, 301, 351, 401, 447]
        # for i in range(1, len(a)):
        #     print(a[i - 1], a[i])
        asyncio.run(self.gather_data(1, 10))

    def groups(self):
        general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
        html = self.session.get(general_url).text
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
                try:
                    Groups(
                        group_name=group.get('data-nm'),
                        group_faculty=Faculties.objects.get(faculty_name=faculty.find(class_='vt253').text.strip()),
                        group_link=group.get('href'),
                    ).save()
                except IntegrityError:
                    pass

    def classes(self):
        general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
        volume = len(Groups.objects.all())
        for i in range(1, volume + 1):
            group = Groups.objects.get(pk=i)
            group_url = self.session.get(general_url + group.group_link + '&date=' + str(group.end_parse)).text
            html = Soup(group_url, 'lxml').find(class_='vt244b').contents
            while len(html) != 0:
                for week in html:
                    time = week.find(
                        class_='vt283').parent.text  # получения тега, содержащего время. Далее разбиваем на два объекта date с началом и концом
                    end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
                    start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
                    for day in week.find_all(class_='vt258'):
                        date_offset = int(day.parent.get('class')[-1][
                                              -1]) - 1  # этот цикл нужен, чтобы иметь возможность добавить два занятия в одну пару
                        # try:
                        name = day.find(class_="vt240").text.strip()
                        type = day.find(class_="vt243").text.strip()
                        teachers = day.find(class_="teacher").text.strip().split(' ')
                        teachers = (lambda a, n=2: [' '.join(a[i:i + n]) for i in range(0, len(a), n)])(
                            teachers)  # превращаем в массив учителей
                        datepush = group.end_parse + datetime.timedelta(
                            days=date_offset)  # дата понедельника + номер текущего дня
                        place = day.find(class_="vt242").text.strip()
                        place = place.split(':')[1].strip().split(';')
                        aud = place[0]
                        building = None
                        if (len(place) == 2):
                            if '/' in place[1]:
                                building = place[1][-1]
                            else:
                                building = 'k'
                        Classes(
                            class_name=name,
                            class_audience=aud,
                            class_building=building,
                            class_type=type,
                            class_date=datepush,
                            class_start=start,
                            class_end=end,
                            class_teachers=teachers,
                            group_id=group,
                        ).save()
                        # except AttributeError:
                        #     pass
                group.end_parse += datetime.timedelta(days=7)
                group.save(update_fields=["end_parse"])
                # Groups.objects.get(group).update(end_parse=F("end_parse") + datetime.timedelta(days=7))
                group_url = self.session.get(general_url + group.group_link + '&date=' + str(group.end_parse)).text
                html = Soup(group_url, 'lxml').find(class_='vt244b').contents


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('obj', type=str, help='Choose the object of parsing: groups, classes')

    def handle(self, *args, **options):
        obj = options['obj']
        if obj == 'groups':
            Parse().groups()
        elif obj == 'classes':

            starttime = time.time()
            Parse().main()
            # Parse().classes()
            print(time.time() - starttime)
        else:
            self.stdout.write('wrong arguments')


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
