# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-07-25 12:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0022_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateField(verbose_name='start')),
                ('end', models.DateField(verbose_name='end')),
            ],
        ),
    ]
