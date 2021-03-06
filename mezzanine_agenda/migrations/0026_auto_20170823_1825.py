# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-08-23 16:25
from __future__ import unicode_literals

from django.db import migrations
import mezzanine.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('mezzanine_agenda', '0025_auto_20170726_1605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='no_price_comments',
            field=mezzanine.core.fields.RichTextField(blank=True, null=True, verbose_name='Price comments'),
        ),
        migrations.AlterField(
            model_name='event',
            name='no_price_comments_en',
            field=mezzanine.core.fields.RichTextField(blank=True, null=True, verbose_name='Price comments'),
        ),
        migrations.AlterField(
            model_name='event',
            name='no_price_comments_fr',
            field=mezzanine.core.fields.RichTextField(blank=True, null=True, verbose_name='Price comments'),
        ),
    ]
