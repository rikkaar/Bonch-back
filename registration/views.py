from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

def index(request):
    return HttpResponse("Добро пожаловать в наше приложение!")

def pageNotFound(request, exception):
    return HttpResponseNotFound('Сорян, нет такой страницы :(')
