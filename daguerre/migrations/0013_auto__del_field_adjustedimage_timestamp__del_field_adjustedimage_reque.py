# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'AdjustedImage.timestamp'
        db.delete_column('daguerre_adjustedimage', 'timestamp')

        # Deleting field 'AdjustedImage.requested_max_height'
        db.delete_column('daguerre_adjustedimage', 'requested_max_height')

        # Deleting field 'AdjustedImage.height'
        db.delete_column('daguerre_adjustedimage', 'height')

        # Deleting field 'AdjustedImage.requested_crop'
        db.delete_column('daguerre_adjustedimage', 'requested_crop_id')

        # Deleting field 'AdjustedImage.requested_max_width'
        db.delete_column('daguerre_adjustedimage', 'requested_max_width')

        # Deleting field 'AdjustedImage.requested_width'
        db.delete_column('daguerre_adjustedimage', 'requested_width')

        # Deleting field 'AdjustedImage.requested_adjustment'
        db.delete_column('daguerre_adjustedimage', 'requested_adjustment')

        # Deleting field 'AdjustedImage.width'
        db.delete_column('daguerre_adjustedimage', 'width')

        # Deleting field 'AdjustedImage.requested_height'
        db.delete_column('daguerre_adjustedimage', 'requested_height')

        # Adding field 'AdjustedImage.requested'
        db.add_column('daguerre_adjustedimage', 'requested',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'AdjustedImage.timestamp'
        db.add_column('daguerre_adjustedimage', 'timestamp',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2013, 5, 18, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_max_height'
        db.add_column('daguerre_adjustedimage', 'requested_max_height',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'AdjustedImage.height'
        db.add_column('daguerre_adjustedimage', 'height',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_crop'
        db.add_column('daguerre_adjustedimage', 'requested_crop',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['daguerre.Area'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_max_width'
        db.add_column('daguerre_adjustedimage', 'requested_max_width',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_width'
        db.add_column('daguerre_adjustedimage', 'requested_width',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_adjustment'
        db.add_column('daguerre_adjustedimage', 'requested_adjustment',
                      self.gf('django.db.models.fields.CharField')(default=0, max_length=255),
                      keep_default=False)

        # Adding field 'AdjustedImage.width'
        db.add_column('daguerre_adjustedimage', 'width',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'AdjustedImage.requested_height'
        db.add_column('daguerre_adjustedimage', 'requested_height',
                      self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True),
                      keep_default=False)

        # Deleting field 'AdjustedImage.requested'
        db.delete_column('daguerre_adjustedimage', 'requested')


    models = {
        'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '300'})
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