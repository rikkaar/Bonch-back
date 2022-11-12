import datetime

from django.db import models, connection
from django.contrib.postgres.fields import ArrayField


class Groups(models.Model):
    group_name = models.CharField(max_length=64, unique=True)
    group_faculty = models.ForeignKey("Faculties", on_delete=models.CASCADE, blank=True, null=True)
    end_parse = models.DateField(default=datetime.date(2022, 9, 1))
    is_parsed = models.BooleanField(default=0)
    group_link = models.CharField(max_length=32, unique=True)
    program_id = models.ForeignKey("Programs", on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = 'Группу'
        verbose_name_plural = 'Группы'


class Faculties(models.Model):
    faculty_name = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.faculty_name

    class Meta:
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'



class Programs(models.Model):
    program_name = models.CharField(max_length=256)


class Classes(models.Model):
    class_name = models.CharField(max_length=128)
    class_audience = models.CharField(max_length=64)
    class_building = models.CharField(max_length=1)
    class_type = models.CharField(max_length=32)
    class_date = models.DateField()
    class_start = models.TimeField()
    class_end = models.TimeField()
    class_teachers = ArrayField(models.CharField(max_length=64))
    group_id = models.ForeignKey("Groups", on_delete=models.CASCADE)
