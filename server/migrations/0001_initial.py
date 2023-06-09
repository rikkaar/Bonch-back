# Generated by Django 4.1.3 on 2023-04-07 14:01

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Faculties',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faculty_name', models.CharField(max_length=32, unique=True)),
            ],
            options={
                'verbose_name': 'Факультет',
                'verbose_name_plural': 'Факультеты',
            },
        ),
        migrations.CreateModel(
            name='Programs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=64, unique=True)),
                ('group_link', models.CharField(max_length=32, unique=True)),
                ('group_faculty', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='server.faculties')),
                ('program_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='server.programs')),
            ],
            options={
                'verbose_name': 'Группу',
                'verbose_name_plural': 'Группы',
            },
        ),
        migrations.CreateModel(
            name='Classes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_name', models.CharField(blank=True, max_length=256, null=True)),
                ('class_audience', models.CharField(blank=True, max_length=64, null=True)),
                ('class_building', models.CharField(blank=True, max_length=8, null=True)),
                ('class_type', models.CharField(blank=True, max_length=32, null=True)),
                ('class_date', models.DateField(blank=True, null=True)),
                ('class_start', models.TimeField(blank=True, null=True)),
                ('class_end', models.TimeField(blank=True, null=True)),
                ('class_teachers', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), blank=True, null=True, size=None)),
                ('group_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='server.groups')),
            ],
        ),
    ]
