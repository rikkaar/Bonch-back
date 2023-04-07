import time
import os
import requests
import datetime
from bs4 import BeautifulSoup as Soup
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.utils import DataError, OperationalError
import asyncio
import aiohttp
import logging

from server.models import Faculties, Groups, Classes

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

logging.basicConfig(level=logging.DEBUG, filename='parser_log.log', filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger()


class Parse:
    async def get_page_data(self, session, link, group):
        credit_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zachetov-studentov-ochnoy-i-vecherney-form-obucheniya'
        headers = {
            'User-Agent': 'Chrome/107.0.0.0 Safari/537.36',
            'Accept-Language': 'ru',
        }

        async with session.get(url=link, headers=headers) as response:
            response_text = await response.text()  # получаем сухой html-код
            html = Soup(response_text, 'lxml').find_all(
                'tr')  # СТАБИЛЬНО. ищем блок с расписанием, и обращаемся к его потомкам. Если их нет, то html = []
            # print(len(html))
            # print(html)
            for i in range(1, len(html)):
                try:

                    line = html[i].contents
                    # print(line)

                    day = datetime.datetime.strptime(line[2 * 0].text.strip()[:10], "%d.%m.%Y")  # День занятия
                    time = line[2 * 1].text.split('-')
                    # print(time)
                    start = datetime.datetime.strptime(time[0][-5:], "%H.%M").time()
                    end = datetime.datetime.strptime(time[1][:5], "%H.%M").time()
                    type = line[2 * 2].text.strip()
                    name = line[2 * 3].text.strip()
                    try:
                        teachers = line[2 * 4].text.strip().split('; ')
                    except AttributeError:
                        teachers = []
                        if name != 'Военная подготовка' and name != 'Строевая подготовка':
                            logging.info(f'{group.group_name, str(time)} ERROR, got []:{link}')
                    # print(teachers)

                    try:
                        building = None
                        place = line[2 * 5].text.split('; ')
                        aud = place[0]
                        if len(place) != 1:
                            try:
                                if place[1][-1] == '3':
                                    building = 'A3'
                                else:
                                    building = 'Б22/' + place[1][-1]
                                # print(building)
                            except IndexError:
                                logging.info(f'{group.group_name, str(time)} NO BUILDING:{link}')
                    except (AttributeError, IndexError) as error:
                        if name == 'ФЗ':
                            aud = 'Спортивные площадки'
                            building = None
                            if name != 'Элективные дисциплины по физической культуре и спорту' and name != 'Физическая культура и спорт':
                                logging.info(f'{group.group_name, str(time)} GOT FZ:{link}')
                        else:
                            aud = None
                            building = None
                            if name != 'Военная подготовка' and name != 'Строевая подготовка':
                                logging.info(f'{group.group_name, str(time)} ERROR, not FZ:{link}')

                    # print(day, start, end, type, name, aud, building)

                    try:
                        Classes(
                            class_name=name,
                            class_audience=aud,
                            class_building=building,
                            class_type=type,
                            class_date=day,
                            class_start=start,
                            class_end=end,
                            class_teachers=teachers,
                            group_id=group,
                        ).save()
                    except UnboundLocalError:
                        logging.exception('DataError')
                        logging.info(f'{group.group_name, str(time), day}')
                        pass
                    # except AttributeError:
                    #     pass
                except AttributeError:
                    print(time, group.group_name)
                    logging.exception('AttributeError')
                    logging.info(f'{group.group_name, str(time), day}')

        # end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
        # start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
        # for day in line.find_all(class_='vt258'):  # СТАБИЛЬНО.
        #     try:
        #         date_offset = int(day.parent.get('class')[-1][
        #                               -1]) - 1  # СТАБИЛЬНО. ['vt239', 'rasp-day', 'rasp-day1'] это особенность bs4.
        #         datepush = start_parse + datetime.timedelta(
        #             days=date_offset)  # дата понедельника + номер текущего дня
        #         name = day.find(class_="vt240").text.strip()  # +-СТАБИЛЬНО.
        #         type = day.find(
        #             class_="vt243").text.strip()  # +-СТАБИЛЬНО - выбирается из списка. Врядли можно не выбрать, хотя....
        #         try:
        #             teachers = day.find(class_="teacher").text.strip().split(' ')  # НЕСТАБИЛЬНО.
        #             teachers = (lambda a, n=2: [' '.join(a[i:i + n]) for i in range(0, len(a), n)])(
        #                 teachers)  # превращаем в массив учителей
        #         except AttributeError:
        #             teachers = []
        #             if name != 'Военная подготовка' and name != 'Строевая подготовка':
        #                 logging.info(f'{group.group_name, str(datepush)} ERROR, got []:{link}')
        #         try:
        #             building = None
        #             place = day.find(class_="vt242").text.strip()  # НЕСТАБИЛЬНО.
        #             place = place.split(':')[1].strip().split(';')
        #             aud = place[0]
        #             if len(place) != 1:
        #                 try:
        #                     building = place[1]
        #                 except IndexError:
        #                     logging.info(f'{group.group_name, str(datepush)} NO BUILDING:{link}')
        #         except (AttributeError, IndexError) as error:
        #             if line.find(class_='vt283').text == 'ФЗ':
        #                 aud = 'Спортивные площадки'
        #                 building = None
        #                 if name != 'Элективные дисциплины по физической культуре и спорту' and name != 'Физическая культура и спорт':
        #                     logging.info(f'{group.group_name, str(datepush)} GOT FZ:{link}')
        #             else:
        #                 aud = None
        #                 building = None
        #                 if name != 'Военная подготовка' and name != 'Строевая подготовка':
        #                     logging.info(f'{group.group_name, str(datepush)} ERROR, not FZ:{link}')
        #         try:
        #             Classes(
        #                 class_name=name,
        #                 class_audience=aud,
        #                 class_building=building,
        #                 class_type=type,
        #                 class_date=datepush,
        #                 class_start=start,
        #                 class_end=end,
        #                 class_teachers=teachers,
        #                 group_id=group,
        #             ).save()
        #         except UnboundLocalError:
        #             logging.exception('DataError')
        #             logging.info(f'{group.group_name, str(datepush), day}')
        #             pass
        #         # except AttributeError:
        #         #     pass
        #     except AttributeError:
        #         print(datepush, group.group_name)
        #         logging.exception('AttributeError')
        #         logging.info(f'{group.group_name, str(datepush), day}')


    async def gather_data(self, pfrom, pto):
        async with aiohttp.ClientSession() as session:
            tasks = []
            credit_url = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zachetov-studentov-ochnoy-i-vecherney-form-obucheniya'
            for i in range(pfrom, pto):
                group = Groups.objects.get(pk=i)
                url = credit_url + group.group_link
                task = asyncio.create_task(self.get_page_data(session, url, group))
                tasks.append(task)
            await asyncio.gather(*tasks)


    def main(self):
        # a = [1, 41, 81, 121, 161, 201, 241, 281, 321, 361, 401, 441, 447]
        # a = [1, 51, 101, 151, 201, 251, 301, 351, 401, 447]
        # for i in range(1, len(a)):
        #     print(a[i - 1], a[i])

        asyncio.run(self.gather_data(1, 30))


class Command(BaseCommand):
    def handle(self, *args, **options):
        Parse().main()
