# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'AdjustedImage', fields ['requested', 'storage_path']
        db.create_index(u'daguerre_adjustedimage', ['requested', 'storage_path'])


    def backwards(self, orm):
        # Removing index on 'AdjustedImage', fields ['requested', 'storage_path']
        db.delete_index(u'daguerre_adjustedimage', ['requested', 'storage_path'])


    models = {
        u'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage', 'index_together': "[['requested', 'storage_path']]"},
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