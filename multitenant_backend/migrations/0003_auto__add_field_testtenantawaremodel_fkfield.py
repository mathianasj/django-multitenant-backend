# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TestTenantAwareModel.fkfield'
        db.add_column('multitenant_testtenantawaremodel', 'fkfield',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['multitenant.TestTenantAwareModel'], null=True, blank=True),
                      keep_default=False)

        # Adding M2M table for field m2mfield on 'TestTenantAwareModel'
        db.create_table('multitenant_testtenantawaremodel_m2mfield', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_testtenantawaremodel', models.ForeignKey(orm['multitenant.testtenantawaremodel'], null=False)),
            ('to_testtenantawaremodel', models.ForeignKey(orm['multitenant.testtenantawaremodel'], null=False))
        ))
        db.create_unique('multitenant_testtenantawaremodel_m2mfield', ['from_testtenantawaremodel_id', 'to_testtenantawaremodel_id'])


    def backwards(self, orm):
        # Deleting field 'TestTenantAwareModel.fkfield'
        db.delete_column('multitenant_testtenantawaremodel', 'fkfield_id')

        # Removing M2M table for field m2mfield on 'TestTenantAwareModel'
        db.delete_table('multitenant_testtenantawaremodel_m2mfield')


    models = {
        'multitenant.tenant': {
            'Meta': {'object_name': 'Tenant'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'multitenant.testtenantawaremodel': {
            'Meta': {'object_name': 'TestTenantAwareModel'},
            'fkfield': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multitenant.TestTenantAwareModel']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'm2mfield': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'m2mfield_rel_+'", 'to': "orm['multitenant.TestTenantAwareModel']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'tenant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['multitenant.Tenant']"})
        }
    }

    complete_apps = ['multitenant']