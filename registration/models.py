import datetime

from django.db import models
from django.contrib.postgres.fields import ArrayField


class Groups(models.Model):
    group_name = models.CharField(max_length=64)
    group_faculty = models.ForeignKey("Faculties", on_delete=models.CASCADE)
    end_parse = models.DateField(default=datetime.date(2022, 9, 1))
    group_link = models.CharField(max_length=32, unique=True)
    program_id = models.ForeignKey("Programs", on_delete=models.CASCADE)


class Faculties(models.Model):
    faculty_name = models.CharField(max_length=32)


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
