# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-06-26 16:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0020_auto_20170626_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventshop',
            name='item_url',
            field=models.CharField(default='https://', max_length=255, verbose_name='Item URL'),
            preserve_default=False,
        ),
    ]