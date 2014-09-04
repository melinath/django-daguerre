# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daguerre', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adjustedimage',
            name='adjusted',
            field=models.ImageField(max_length=45, upload_to=b'daguerre/%Y/%m/%d/'),
        ),
    ]
