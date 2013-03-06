# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Area', fields ['y1', 'x2', 'x1', 'y2', 'storage_path']
        db.delete_unique('daguerre_area', ['y1', 'x2', 'x1', 'y2', 'storage_path'])

        # Removing index on 'Area', fields ['storage_path']
        db.delete_index('daguerre_area', ['storage_path'])

        # Removing index on 'AdjustedImage', fields ['requested_width']
        db.delete_index('daguerre_adjustedimage', ['requested_width'])

        # Removing index on 'AdjustedImage', fields ['requested_adjustment']
        db.delete_index('daguerre_adjustedimage', ['requested_adjustment'])

        # Removing index on 'AdjustedImage', fields ['height']
        db.delete_index('daguerre_adjustedimage', ['height'])

        # Removing index on 'AdjustedImage', fields ['width']
        db.delete_index('daguerre_adjustedimage', ['width'])

        # Removing index on 'AdjustedImage', fields ['requested_height']
        db.delete_index('daguerre_adjustedimage', ['requested_height'])

        # Removing index on 'AdjustedImage', fields ['requested_max_width']
        db.delete_index('daguerre_adjustedimage', ['requested_max_width'])

        # Removing index on 'AdjustedImage', fields ['requested_max_height']
        db.delete_index('daguerre_adjustedimage', ['requested_max_height'])

        # Removing index on 'AdjustedImage', fields ['storage_path']
        db.delete_index('daguerre_adjustedimage', ['storage_path'])


    def backwards(self, orm):
        # Adding index on 'AdjustedImage', fields ['storage_path']
        db.create_index('daguerre_adjustedimage', ['storage_path'])

        # Adding index on 'AdjustedImage', fields ['requested_max_height']
        db.create_index('daguerre_adjustedimage', ['requested_max_height'])

        # Adding index on 'AdjustedImage', fields ['requested_max_width']
        db.create_index('daguerre_adjustedimage', ['requested_max_width'])

        # Adding index on 'AdjustedImage', fields ['requested_height']
        db.create_index('daguerre_adjustedimage', ['requested_height'])

        # Adding index on 'AdjustedImage', fields ['width']
        db.create_index('daguerre_adjustedimage', ['width'])

        # Adding index on 'AdjustedImage', fields ['height']
        db.create_index('daguerre_adjustedimage', ['height'])

        # Adding index on 'AdjustedImage', fields ['requested_adjustment']
        db.create_index('daguerre_adjustedimage', ['requested_adjustment'])

        # Adding index on 'AdjustedImage', fields ['requested_width']
        db.create_index('daguerre_adjustedimage', ['requested_width'])

        # Adding index on 'Area', fields ['storage_path']
        db.create_index('daguerre_area', ['storage_path'])

        # Adding unique constraint on 'Area', fields ['y1', 'x2', 'x1', 'y2', 'storage_path']
        db.create_unique('daguerre_area', ['y1', 'x2', 'x1', 'y2', 'storage_path'])


    models = {
        'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_adjustment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'requested_crop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['daguerre.Area']", 'null': 'True', 'blank': 'True'}),
            'requested_height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'requested_max_height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'requested_max_width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'requested_width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'daguerre.area': {
            'Meta': {'ordering': "('priority',)", 'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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