# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Area', fields ['y1', 'x2', 'image', 'x1', 'y2']
        db.delete_unique('daguerre_area', ['y1', 'x2', 'image_id', 'x1', 'y2'])

        # Deleting field 'Area.image'
        db.delete_column('daguerre_area', 'image_id')

        # Adding unique constraint on 'Area', fields ['y1', 'x2', 'x1', 'y2', 'storage_path']
        db.create_unique('daguerre_area', ['y1', 'x2', 'x1', 'y2', 'storage_path'])


    def backwards(self, orm):
        # Removing unique constraint on 'Area', fields ['y1', 'x2', 'x1', 'y2', 'storage_path']
        db.delete_unique('daguerre_area', ['y1', 'x2', 'x1', 'y2', 'storage_path'])

        # Adding field 'Area.image'
        db.add_column('daguerre_area', 'image',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='areas', to=orm['daguerre.Image']),
                      keep_default=False)

        # Adding unique constraint on 'Area', fields ['y1', 'x2', 'image', 'x1', 'y2']
        db.create_unique('daguerre_area', ['y1', 'x2', 'image_id', 'x1', 'y2'])


    models = {
        'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_adjustment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'requested_crop': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['daguerre.Area']", 'null': 'True', 'blank': 'True'}),
            'requested_height': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'requested_max_height': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'requested_max_width': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'requested_width': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'daguerre.area': {
            'Meta': {'ordering': "('priority',)", 'unique_together': "(('storage_path', 'x1', 'y1', 'x2', 'y2'),)", 'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_index': 'True'}),
            'x1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'x2': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y2': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'daguerre.image': {
            'Meta': {'object_name': 'Image'},
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['daguerre']