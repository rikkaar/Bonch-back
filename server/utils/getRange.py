# если парсим все, то указываем 1 all
# работаем именно с id группы, а не индексом итерации, пусть вышестоящая функция сама думает, как ей обратботать эти id
import asyncio

from server.models import Groups


def getRange(start, end, parse_start, parse_end, nextfunc):
    print(start, end, parse_start, parse_end)
    offset = 5
    if end == "all":
        end = Groups.objects.count()
    while start <= end:
        if start + offset - 1 >= end:  #  тут мы проверяем будет ли следующий шаг больше една? Если да, то конечной точкой будет сам end
            asyncio.run(nextfunc(start, end, parse_start, parse_end))
        else:
            if start == end: # если мы дошли до того, что start == end, то нужно вывести start, start + 1 (Чтобы в range попало одно значение)
                asyncio.run(nextfunc(start, start, parse_start, parse_end))
            else:
                asyncio.run(nextfunc(start, start + offset - 1, parse_start, parse_end)) # Если все-таки мы двигаемся с начала, то можно указать настоящий и слудеющий предел
        start += offset
