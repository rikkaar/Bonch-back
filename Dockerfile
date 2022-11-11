FROM python:3.10.7-alpine
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /django

#RUN apk update \
#    && apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python manage.py makemigrations;python manage.py migrate;python manage.py runserver 0.0.0.0:8000