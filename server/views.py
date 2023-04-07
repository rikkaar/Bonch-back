from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render

def index(request):
    return JsonResponse({'status': "ok"})
    return HttpResponse("Добро пожаловать в наше приложение!")


def pageNotFound(request, exception):
    return HttpResponseNotFound('Сорян, нет такой страницы :(')