import os

import requests
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        link = 'https://lk.sut.ru/cabinet/lib/autentificationok.php'
        login = os.environ.get('TEST_LOGIN')
        password = os.environ.get('TEST_PASSWORD')
        loginlink = f'https://lk.sut.ru/cabinet/lib/autentificationok.php?users={login}&parole={password}'
        session = requests.Session()
        headers = {
            'User-Agent': 'Chrome/107.0.0.0 Safari/537.36'
        }

        data = {
            'users': os.environ.get('TEST_LOGIN'),
            'parole': os.environ.get('TEST_PASSWORD')
        }


        try:
            response = session.post(link, data=data, headers=headers)
            # response = session.get(loginlink, headers=headers)
            print(response)
            cookies_dict = [
                # {"__ddg1_": key.__ddg1_, "cookie": key.cookie, "miden": key.miden, "uid": key.uid}
                {"domain": key.domain, "name": key.name, "path": key.path, "value": key.value}
                for key in session.cookies
            ]
            session2 = requests.Session()
            for coockies in cookies_dict:
                session2.cookies.set(**coockies)
            print("начали")
            resp = session2.get('https://lk.sut.ru/cabinet/?login=yes', headers=headers).text
            print(resp)
            print("закончили")
        except requests.exceptions.TooManyRedirects:
            print("нахуй иди")
            pass
