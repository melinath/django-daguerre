# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        adjusted_images = orm['daguerre.adjustedimage'].objects.all()
        for adjusted_image in adjusted_images:
            adjusted_image.storage_path = adjusted_image.image.storage_path
            adjusted_image.save()

    def backwards(self, orm):
        "Write your backwards methods here."
        adjusted_images = orm['daguerre.adjustedimage'].objects.all()
        for adjusted_image in adjusted_images:
            try:
                image = orm['daguerre.image'].objects.filter(storage_path=adjusted_image.storage_path)[:1][0]
            except IndexError:
                adjusted_image.delete()
            else:
                adjusted_image.image = image
                adjusted_image.save()

    models = {
        'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['daguerre.Image']"}),
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
            'Meta': {'ordering': "('priority',)", 'unique_together': "(('image', 'x1', 'y1', 'x2', 'y2'),)", 'object_name': 'Area'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'areas'", 'to': "orm['daguerre.Image']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
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
    symmetrical = True
