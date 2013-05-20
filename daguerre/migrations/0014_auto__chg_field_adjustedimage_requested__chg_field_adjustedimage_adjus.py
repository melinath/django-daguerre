# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'AdjustedImage.requested'
        db.alter_column('daguerre_adjustedimage', 'requested', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'AdjustedImage.adjusted'
        db.alter_column('daguerre_adjustedimage', 'adjusted', self.gf('django.db.models.fields.files.ImageField')(max_length=45))

        # Changing field 'AdjustedImage.storage_path'
        db.alter_column('daguerre_adjustedimage', 'storage_path', self.gf('django.db.models.fields.CharField')(max_length=200))

    def backwards(self, orm):

        # Changing field 'AdjustedImage.requested'
        db.alter_column('daguerre_adjustedimage', 'requested', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'AdjustedImage.adjusted'
        db.alter_column('daguerre_adjustedimage', 'adjusted', self.gf('django.db.models.fields.files.ImageField')(max_length=255))

        # Changing field 'AdjustedImage.storage_path'
        db.alter_column('daguerre_adjustedimage', 'storage_path', self.gf('django.db.models.fields.CharField')(max_length=300))

    models = {
        'daguerre.adjustedimage': {
            'Meta': {'object_name': 'AdjustedImage'},
            'adjusted': ('django.db.models.fields.files.ImageField', [], {'max_length': '45'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'storage_path': ('django.db.models.fields.CharField', [], {'max_length': '200'})
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