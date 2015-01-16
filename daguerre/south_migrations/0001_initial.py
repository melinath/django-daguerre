# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Area'
        db.create_table(u'daguerre_area', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('storage_path', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('x1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('x2', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y2', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('priority', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
        ))
        db.send_create_signal(u'daguerre', ['Area'])

        # Adding model 'AdjustedImage'
        db.create_table(u'daguerre_adjustedimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('storage_path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('adjusted', self.gf('django.db.models.fields.files.ImageField')(max_length=45)),
            ('requested', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'daguerre', ['AdjustedImage'])


    def backwards(self, orm):
        # Deleting model 'Area'
        db.delete_table(u'daguerre_area')

        # Deleting model 'AdjustedImage'
        db.delete_table(u'daguerre_adjustedimage')


    models = {
        u'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '45'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'daguerre.area': {
            'Meta': {'ordering': "('priority',)", 'object_name': 'Area'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'x1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'x2': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y2': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['daguerre']