from bs4 import BeautifulSoup
import requests
import datetime
import connection
from registration.models import Groups

conn = connection.GetConnection()
cur = connection.GetCursor(conn)

base_url_general = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'

html_base_url_general = requests.post(base_url_general, headers={"User-Agent": "Chrome/106.0.0.0"}).text
parsed_base_url_general = BeautifulSoup(html_base_url_general, 'lxml')
for faculty in parsed_base_url_general.find_all(class_='vt252'):
    fac = faculty.find(class_='vt253').text.strip()
    for group in faculty.find_all(class_='vt256'):
        Groups.objects.create()
        # cur.execute('''
        # INSERT INTO public.group (group_name, group_faculty, group_link, end_parse)
        # VALUES (%s, %s, %s, %s)
        # ON CONFLICT (group_name) DO UPDATE SET
        # (group_faculty, group_link, end_parse) = (EXCLUDED.group_faculty, EXCLUDED.group_link, EXCLUDED.end_parse)''',
        #             [str(group.get('data-nm')), str(fac), str(group.get('href')), datetime.date(2022, 9, 1)])
        # conn.commit()
conn.close()