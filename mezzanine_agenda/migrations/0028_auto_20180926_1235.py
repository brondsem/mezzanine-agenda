# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2018-09-26 10:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0027_auto_20180918_1524'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('rank', 'start'), 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
    ]