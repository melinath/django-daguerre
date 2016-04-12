# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daguerre', '0002_auto_20140904_2006'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='adjustedimage',
            index_together=set([('requested', 'storage_path')]),
        ),
    ]
