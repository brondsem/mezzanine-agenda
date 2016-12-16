# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2016-12-16 14:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0015_auto_20161021_1937'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventlocation',
            name='city',
            field=models.CharField(default='', max_length=255, verbose_name='city'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventlocation',
            name='postal_code',
            field=models.CharField(default='', max_length=16, verbose_name='postal code'),
            preserve_default=False,
        ),
    ]