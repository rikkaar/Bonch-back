from django.contrib import admin

from server.models import *


@admin.register(Faculties)
class FacultiesAdmin(admin.ModelAdmin):
    list_display = ('pk', 'faculty_name',)


@admin.register(Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'group_name', 'group_faculty', 'group_link', 'program_id',)
