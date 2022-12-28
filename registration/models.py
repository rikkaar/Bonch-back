import datetime

from django.db import models, connection
from django.contrib.postgres.fields import ArrayField


class Groups(models.Model):
    group_name = models.CharField(max_length=64, unique=True)
    group_faculty = models.ForeignKey("Faculties", on_delete=models.CASCADE, blank=True, null=True)
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
    class_name = models.CharField(max_length=256, blank=True, null=True)
    class_audience = models.CharField(max_length=64, blank=True, null=True)
    class_building = models.CharField(max_length=8, blank=True, null=True)
    class_type = models.CharField(max_length=32, blank=True, null=True)
    class_date = models.DateField(blank=True, null=True)
    class_start = models.TimeField(blank=True, null=True)
    class_end = models.TimeField(blank=True, null=True)
    class_teachers = ArrayField(models.CharField(max_length=64), blank=True, null=True)
    group_id = models.ForeignKey("Groups", on_delete=models.CASCADE, blank=True, null=True)
