# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-02-22 09:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0016_auto_20161216_1558'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('rank', 'start'), 'verbose_name': 'Event', 'verbose_name_plural': 'Events'},
        ),
        migrations.AddField(
            model_name='event',
            name='rank',
            field=models.IntegerField(blank=True, null=True, verbose_name='rank'),
        ),
    ]
