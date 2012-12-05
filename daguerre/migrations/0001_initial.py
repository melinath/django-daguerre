# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Image'
        db.create_table('daguerre_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=255)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('daguerre', ['Image'])

        # Adding model 'Area'
        db.create_table('daguerre_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(related_name='areas', to=orm['daguerre.Image'])),
            ('x1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('x2', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y2', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('priority', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
        ))
        db.send_create_signal('daguerre', ['Area'])

        # Adding unique constraint on 'Area', fields ['image', 'x1', 'y1', 'x2', 'y2']
        db.create_unique('daguerre_area', ['image_id', 'x1', 'y1', 'x2', 'y2'])

        # Adding model 'AdjustedImage'
        db.create_table('daguerre_adjustedimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['daguerre.Image'])),
            ('adjusted', self.gf('django.db.models.fields.files.ImageField')(max_length=255)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('requested_width', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('requested_height', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('requested_max_width', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('requested_max_height', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('requested_adjustment', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('requested_crop', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['daguerre.Area'], null=True, blank=True)),
        ))
        db.send_create_signal('daguerre', ['AdjustedImage'])

        # Adding unique constraint on 'AdjustedImage', fields ['image', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment']
        db.create_unique('daguerre_adjustedimage', ['image_id', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment'])


    def backwards(self, orm):
        # Removing unique constraint on 'AdjustedImage', fields ['image', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment']
        db.delete_unique('daguerre_adjustedimage', ['image_id', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment'])

        # Removing unique constraint on 'Area', fields ['image', 'x1', 'y1', 'x2', 'y2']
        db.delete_unique('daguerre_area', ['image_id', 'x1', 'y1', 'x2', 'y2'])

        # Deleting model 'Image'
        db.delete_table('daguerre_image')

        # Deleting model 'Area'
        db.delete_table('daguerre_area')

        # Deleting model 'AdjustedImage'
        db.delete_table('daguerre_adjustedimage')


    models = {
        'daguerre.adjustedimage': {
            'Meta': {'unique_together': "(('image', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment'),)", 'object_name': 'AdjustedImage'},
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
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['daguerre']