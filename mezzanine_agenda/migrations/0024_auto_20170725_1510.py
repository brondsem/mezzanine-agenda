# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-07-25 13:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0023_season'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='season',
            options={'verbose_name': 'Season', 'verbose_name_plural': 'Seasons'},
        ),
        migrations.AddField(
            model_name='season',
            name='title',
            field=models.CharField(default='', max_length=512, verbose_name='name'),
            preserve_default=False,
        ),
    ]