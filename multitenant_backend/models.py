"""
To make a tenant-aware model, simply subclass django-multitenant's TenantModel.
example:

    from django.db import models
    from multitenant.models import TenantModel

    class BugReport(TenantModel)
        description = models.CharField(max_length=200)

TenantModels have a tenant-aware manager called tenant_objects:

    bugs = BugReport.tenant_objects.all()

This will bring up all instances owned by the "current tenant".
The current tenant, for a given request, is determined by checking the tenant field
of the user profile for request.user.
If it's an anonymous user, the current tenant will be the base tenant.
"""

from django.apps import apps
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.conf import settings    # We look at DEBUG only, from settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import related_lookups
from django.db.models import lookups

from multitenant_backend.settings import BASE_TENANT_ID


class TenantMgr(models.Manager):
    def get_queryset(self):
        tenant = Tenant()
        if tenant:
            return super(TenantMgr, self).get_queryset().filter(tenant="{{tenant_id}}")
        else:
            return super(TenantMgr, self).get_queryset()


class Tenant(models.Model):
    """
    This is the key model used to manage multitenancy.
    Many tenants will use the database at the same time; any model that must be tenant-specific will need
    a foreign-key relation to Tenant.

    It is critical that the "user profile" model also have a foreign key relation to Tenant.
    """
    name = models.CharField(
        max_length = 255,
        unique = True,
    )
    email = models.EmailField()
    def __unicode__(self):
        return self.name

    def get_by_natural_key(self, name):
        return self.get(name=name)


class RelatedExact(related_lookups.RelatedLookupMixin, lookups.Exact):
    def get_prep_lookup(self):
        return "{{tenant_id}}"


class TenantForeignKey(models.ForeignKey):
    def get_lookup(self, lookup_name):
        print('captured {}'.format(lookup_name))
        return RelatedExact
        
    def get_db_prep_save(self, value, connection):
        return "{{tenant_id}}"

class TenantModel(models.Model):
    tenant = TenantForeignKey(Tenant)

    # Django gives special treatment to the first Manager declared within a Model; it becomes the default manager.
    # There are some corner cases when you don't want the tenant-aware manager to be the default one, for example
    # when running django management commands.
    objects = TenantMgr()
    tenant_objects = TenantMgr()
    
    
    
    def save(self, *args, **kwargs):
        if hasattr(self, 'tenant_id') and not ( isinstance(self, UserProfile) ):
            self.tenant = Tenant(id='{{tenant_id}}')
        
        super(TenantModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True

class UserProfile(TenantModel):
    user = models.OneToOneField(User)


def clone_model_instance(instance, new_values={}):
    """
    WARNING: This function will NOT clone the instance's m2m fields if there are any.
    It relies on django magic; when you try to save an instance with no pk, django uses INSERT instead of UPDATE.
    """
    instance.id = None
    for k in new_values.keys():
        if k != 'id':
            setattr(instance, k, new_values[k])
    instance.save()
    return instance


def clone_base_tenant(sender, instance, created, **kwargs):
    """
    Runs through all tenant-informed models, and copies each base tenant instance to an instance for the current tenant.
    """

    # Don't clone anything when loading fixtures (when raw==True)
    if created and not kwargs.get('raw', False):

        all_model_classes = apps.get_models()

        for model_class in all_model_classes:
            if issubclass(model_class, TenantModel) and not issubclass(model_class, UserProfile):
                qs = model_class.objects.filter(tenant=BASE_TENANT_ID).order_by('id')
                for i in qs:
                    clone_model_instance(i, { 'tenant': instance })

post_save.connect(clone_base_tenant, sender=Tenant)


def clone_model(model_class, source_tenant=BASE_TENANT_ID, dest_tenant='current_tenant'):
    """
    This is a general-purpose tool to clone (copy) all instances of a model from one tenant to another.
    By default, it clones from the base tenant to the current tenant (logged in user).
    Warning: it will NOT work with m2m fields.
    """
    if dest_tenant == 'current_tenant':
        dest_tenant = get_current_tenant()

    if issubclass(model_class, TenantModel):
        qs = model_class.objects.filter(tenant=source_tenant).order_by('id')
        for i in qs:
            clone_model_instance(i, { 'tenant': dest_tenant })


def get_profile_class_old():
    # Determine what is the Model Class that holds user profiles:
    users = User.objects.all()
    if users:
        return users[0].get_profile().__class__
    else:
        return None


