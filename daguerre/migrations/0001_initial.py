# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdjustedImage',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('storage_path', models.CharField(max_length=200)),
                ('adjusted', models.ImageField(upload_to='daguerre/%Y/%m/%d/')),
                ('requested', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('storage_path', models.CharField(max_length=300)),
                ('x1', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('y1', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('x2', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('y2', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('name', models.CharField(max_length=20, blank=True)),
                ('priority', models.PositiveIntegerField(default=3, validators=[django.core.validators.MinValueValidator(1)])),
            ],
            options={
                u'ordering': ('priority',),
            },
            bases=(models.Model,),
        ),
    ]
