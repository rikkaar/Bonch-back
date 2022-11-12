import datetime
import requests
from bs4 import BeautifulSoup
import connection

conn = connection.GetConnection()
cur = connection.GetCursor(conn)

base_url_general = 'https://www.sut.ru/studentu/raspisanie/raspisanie-zanyatiy-studentov-ochnoy-i-vecherney-form-obucheniya'


def parse_group_by_name(name):
    cur.execute('''
        SELECT group_name, group_link, end_parse, group_id FROM public.group WHERE group_name = (%s);
        ''', [name])
    rec = cur.fetchone()
    group_link = rec.group_link  # для проходки по одной группе остается константой
    end_parse = rec.end_parse  # извлекается один раз и запускается в цикл
    group_id = rec.group_id  # для проходки по одной группе остается константой

    html_group = requests.post(base_url_general + group_link + '&date=' + str(end_parse),
                               headers={"User-Agent": "Chrome/106.0.0.0"}).text

    bs_html_group = BeautifulSoup(html_group, 'lxml').find(
        class_='vt244b').contents  # получение интерактивной страницы. Далее в цикле эта операция будет повторяться для каждой новой страницы
    while len(bs_html_group) != 0:
        for elem in bs_html_group:
            time = elem.find(
                class_='vt283').parent.text  # получения тега, содержащего время. Далее разбиваем на два объекта date с началом и концом
            end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
            start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
            for d in elem.find_all(class_='vt258'):
                count = int(d.parent.get('class')[-1][
                                -1]) - 1  # этот цикл нужен, чтобы иметь возможность добавить два занятия в одну пару
                try:
                    name = d.find(class_="vt240").text.strip()
                    type = d.find(class_="vt243").text.strip()
                    teachers = d.find(class_="teacher").text.strip().split(' ')
                    teachers = (lambda a, n=2: [' '.join(a[i:i + n]) for i in range(0, len(a), n)])(
                        teachers)  # превращаем в массив учителей
                    datepush = end_parse + datetime.timedelta(days=count)  # дата понедельника + номер текущего дня
                    place = d.find(class_="vt242").text.strip()
                    place = place.split(':')[1].strip().split(';')
                    aud = place[0]
                    corpus = None
                    if (len(place) == 2):
                        if '/' in place[1]:
                            corpus = place[1][-1]
                        else:
                            corpus = 'k'
                    cur.execute('''
                    INSERT INTO CLASS (class_name, class_audience, class_korpus, class_type, class_date, class_start, class_end, class_teachers, group_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    ''',
                                [name, aud, corpus, type, datepush, start, end, teachers, group_id])
                    conn.commit()
                except AttributeError:
                    pass
        end_parse += datetime.timedelta(days=7)
        cur.execute('''
        UPDATE public.group
        SET end_parse = (%s)
        WHERE group_id = (%s)
        ''', [end_parse, group_id, ])

        html_group = requests.post(base_url_general + group_link + '&date=' + str(end_parse),
                                   headers={"User-Agent": "Chrome/106.0.0.0"}).text
        bs_html_group = BeautifulSoup(html_group, 'lxml').find(class_='vt244b').contents


def parse_all():
    cur.execute('''
    SELECT COUNT(*) FROM public.group
    ''')
    volume = cur.fetchone().count
    for i in range(1, volume):  # каждой группе по одной итерации
        print(i)
        cur.execute('''
        SELECT group_link, end_parse, group_id FROM public.group WHERE group_id = (%s);
        ''', [i + 1])
        rec = cur.fetchone()
        group_link = rec.group_link  # для проходки по одной группе остается константой
        end_parse = rec.end_parse  # извлекается один раз и запускается в цикл
        group_id = rec.group_id  # для проходки по одной группе остается константой

        html_group = requests.post(base_url_general + group_link + '&date=' + str(end_parse),
                                   headers={"User-Agent": "Chrome/106.0.0.0"}).text

        bs_html_group = BeautifulSoup(html_group, 'lxml').find(
            class_='vt244b').contents  # получение интерактивной страницы. Далее в цикле эта операция будет повторяться для каждой новой страницы
        while len(bs_html_group) != 0:
            for elem in bs_html_group:
                time = elem.find(
                    class_='vt283').parent.text  # получения тега, содержащего время. Далее разбиваем на два объекта date с началом и концом
                end = datetime.datetime.strptime(time[-5::], "%H:%M").time()
                start = datetime.datetime.strptime(time[-10:-5], "%H:%M").time()
                for d in elem.find_all(class_='vt258'):
                    count = int(d.parent.get('class')[-1][
                                    -1]) - 1  # этот цикл нужен, чтобы иметь возможность добавить два занятия в одну пару
                    try:
                        name = d.find(class_="vt240").text.strip()
                        type = d.find(class_="vt243").text.strip()
                        teachers = d.find(class_="teacher").text.strip().split(' ')
                        teachers = (lambda a, n=2: [' '.join(a[i:i + n]) for i in range(0, len(a), n)])(
                            teachers)  # превращаем в массив учителей
                        datepush = end_parse + datetime.timedelta(days=count)  # дата понедельника + номер текущего дня
                        place = d.find(class_="vt242").text.strip()
                        place = place.split(':')[1].strip().split(';')
                        aud = place[0]
                        corpus = None
                        if (len(place) == 2):
                            if '/' in place[1]:
                                corpus = place[1][-1]
                            else:
                                corpus = 'k'
                        cur.execute('''
                        INSERT INTO CLASS (class_name, class_audience, class_korpus, class_type, class_date, class_start, class_end, class_teachers, group_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                        ''',
                                    [name, aud, corpus, type, datepush, start, end, teachers, group_id])
                        conn.commit()
                    except AttributeError:
                        pass
            end_parse += datetime.timedelta(days=7)
            cur.execute('''
            UPDATE public.group
            SET end_parse = (%s)
            WHERE group_id = (%s)
            ''', [end_parse, group_id, ])

            html_group = requests.post(base_url_general + group_link + '&date=' + str(end_parse),
                                       headers={"User-Agent": "Chrome/106.0.0.0"}).text
            bs_html_group = BeautifulSoup(html_group, 'lxml').find(class_='vt244b').contents


# parse_group_by_name('ИСТ-133')
# parse_all()
cur.close()
conn.close()
quit('done')
