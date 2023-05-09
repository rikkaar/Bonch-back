import time
import os
import requests
import datetime
from bs4 import BeautifulSoup as Soup
from django.core.management.base import BaseCommand
from django.db import IntegrityError, OperationalError
import asyncio
import aiohttp
import logging

from server.utils import getRange
from server.models import Faculties, Groups, Classes

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

logging.basicConfig(level=logging.DEBUG, filename='parser_log.log', filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()


class Parse:
    def __init__(self):
        self.session = requests.session()
        self.session.headers = {
            'User-Agent': 'Chrome/107.0.0.0 Safari/537.36',
            'Accept-Language': 'ru',
        }

    async def get_page_data(self, session, link, group, start_parse):
        async with session.get(url=link, headers=self.session.headers) as response:
            response_text = await response.text()  # получаем сухой html-код
            html = Soup(response_text, 'lxml').find(
                class_='vt244b').contents  # СТАБИЛЬНО. ищем блок с расписанием, и обращаемся к его потомкам. Если их нет, то html = []
            for week in html:  # если есть хотя бы одна пара, то цикл запустится, если поле пустое, то ничего не произойдет
                time = week.find(
                    class_='vt283').parent.text  # СТАБИЛЬНО. получения тега, содержащего время. Далее разбиваем на два объекта date с началом и концом пары
                end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
                start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
                for day in week.find_all(class_='vt258'):  # СТАБИЛЬНО.
                    try:
                        date_offset = int(day.parent.get('class')[-1][
                                              -1]) - 1  # СТАБИЛЬНО. ['vt239', 'rasp-day', 'rasp-day1'] это особенность bs4.
                        datepush = start_parse + datetime.timedelta(
                            days=date_offset)  # дата понедельника + номер текущего дня
                        name = day.find(class_="vt240").text.strip()  # +-СТАБИЛЬНО.
                        type = day.find(
                            class_="vt243").text.strip()  # +-СТАБИЛЬНО - выбирается из списка. Врядли можно не выбрать, хотя....
                        try:
                            teachers = day.find(class_="teacher").text.strip().split(' ')  # НЕСТАБИЛЬНО.
                            teachers = (lambda a, n=2: [' '.join(a[i:i + n]).replace(";", '') for i in range(0, len(a), n)])(
                                teachers)  # превращаем в массив учителей
                        except AttributeError:
                            teachers = []
                            if name != 'Военная подготовка' and name != 'Строевая подготовка':
                                logging.info(f'{group.group_name, str(datepush)} ERROR, got []:{link}')
                        try:
                            building = None
                            place = day.find(class_="vt242").text.strip()  # НЕСТАБИЛЬНО.
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
                            obj, created = Classes.objects.get_or_create(
                                class_name=name,
                                class_audience=aud,
                                class_building=building,
                                class_type=type,
                                class_date=datepush,
                                class_start=start,
                                class_end=end,
                                class_teachers=teachers,
                                group_id=group,
                            )
                            # if created:
                            #    logging.info(f'{"Создана запись с id", obj.id, ". Дата: ", str(datepush)}')
                        except UnboundLocalError:
                            logging.exception('DataError')
                            logging.error(f'{group.group_name, str(datepush), day}')
                        # except OperationalError:
                        #     logging.error(f'{"OperationalError"}')
                    except AttributeError:
                        print(datepush, group.group_name)
                        logging.exception('AttributeError')
                        logging.info(f'{group.group_name, str(datepush), day}')

    async def gather_data(self, pfrom, pto, start_parse, end_parse):
        # print(pfrom, pto, start_parse, end_parse)
        async with aiohttp.ClientSession() as session:
            tasks = []
            general_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'
            for i in range(pfrom, pto + 1): # Мы собираем все Группы от и до какого-то id. ЕСЛИ УКАЗАТЬ ДВА ОДИНАКОВЫХ ЗНАЧЕНИЯ, ТО БУДЕТ ПАРСИНГ ОДНОЙ КОНКРЕТНОЙ ГРУППЫ
                group = Groups.objects.get(pk=i)
                while_start_parse = start_parse
                while end_parse >= while_start_parse:
                    url = general_url + group.group_link + '&date=' + str(while_start_parse)
                    task = asyncio.create_task(self.get_page_data(session, url, group, while_start_parse))
                    tasks.append(task)
                    while_start_parse += datetime.timedelta(days=7)
            await asyncio.gather(*tasks)

    def main(self, gfrom, gto, tfrom, tto):
        print("FROM MAIN FUNCTION", gfrom, gto, tfrom, tto)
        getRange.getRange(gfrom, gto, tfrom, tto, self.gather_data)

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
        parser.add_argument('-gfrom', type=int, default=1)
        parser.add_argument('-gto', type=int)
        parser.add_argument('-tfrom', type=str)
        parser.add_argument('-tto', type=str)
        parser.add_argument('-group', type=str)
        parser.add_argument('-time', type=str)

    def handle(self, *args, **options):
        gfrom = options['gfrom']
        gto = options['gto']
        tfrom = options['tfrom']
        tto = options['tto']

        group = options['group']
        timeq = options['time']

        obj = options['obj']
        if obj == 'groups':
            Parse().groups()
        elif obj == 'classes':
            starttime = time.time()
            if group:
                if group == "all":
                    gto = 'all'

                else: gfrom, gto = group, group
            if timeq:
                if timeq == 'all':
                    if (datetime.datetime.now().month <= 7):
                        tfrom = datetime.date(datetime.datetime.now().year, 2, 1)
                        tto = datetime.date(datetime.datetime.now().year, 8, 1)
                    else:
                        tfrom = datetime.date(datetime.datetime.now().year, 9, 1)
                        tto = datetime.date(datetime.datetime.now().year, 2, 1)
                else:
                    tfrom, tto = timeq, timeq
                    tto = datetime.datetime.strptime(tto,
                                                     '%Y-%m-%d').date()  # Выбираем либо дефолтное (конец года?), либо парсим то, что указано пользователем
                    tfrom = datetime.datetime.strptime(tfrom, '%Y-%m-%d').date()
                    tfrom = datetime.datetime.fromisocalendar(tfrom.year, tfrom.isocalendar().week,
                                                              1).date()  # выбор понедельника для выбранной недели начала парсинга


            else:
                tto = datetime.datetime.strptime(tto,
                                             '%Y-%m-%d').date()  # Выбираем либо дефолтное (конец года?), либо парсим то, что указано пользователем
                tfrom = datetime.datetime.strptime(tfrom, '%Y-%m-%d').date()
                tfrom = datetime.datetime.fromisocalendar(tfrom.year, tfrom.isocalendar().week,
                                                      1).date()  # выбор понедельника для выбранной недели начала парсинга

            Parse().main(gfrom, gto, tfrom, tto)
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
