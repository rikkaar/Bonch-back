# Generated by Django 4.1.3 on 2022-11-12 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_remove_groups_is_parsed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classes',
            name='class_building',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
    ]
