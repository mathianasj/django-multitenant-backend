
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local
    
from django.db import connection
    
from multitenant_backend import models
from django.core import exceptions as djangoexceptions
from multitenant_backend.settings import CREATE_MISSING_TENANT

import logging
import uuid

logger = logging.getLogger("multitenant")

_thread_locals = local()



def set_tenant_to_default():
    """
    Sets the current tenant as per BASE_TENANT_ID.
    """
    # import is done from within the function, to avoid trouble 
    from multitenant_backend.models import Tenant, BASE_TENANT_ID
    set_current_tenant( Tenant.objects.get(id=BASE_TENANT_ID) )
    

def set_current_tenant(tenant):
    logger.info("setting tenant to thread local")
    logger.debug("settting tenant {} to thread local".format(tenant))
    setattr(_thread_locals, 'tenant', tenant)
    connection.set_tenant(tenant)
    

def get_current_tenant():
    logger.info("getting tenant from thread local")
    return _thread_locals.tenant


class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        # add request id
        request.request_id = str(uuid.uuid4())
    
        connection.set_schema_to_public()
    
        logger.info('incoming request')
        user = getattr(request, 'user', None)
        
        # Attempt to set tenant
        print("user: {}".format(user))
        if user and not user.is_anonymous():
            logging.info("try to find user profile")
            
            email = user.email
            domain = email.split("@")[1]
            
            if(CREATE_MISSING_TENANT):
                tenant, created = models.Tenant.objects.update_or_create(name=domain, defaults={
                    'name':domain,
                    'email':email
                })
            else:
                tenant = models.Tenant.objects.get(name=domain)
            
            set_current_tenant(tenant)
            
            try:
                profile = user.userprofile
                logger.debug("profile {}".format(profile.tenant.pk))
                if profile:
                    logger.info("setting tenant")
                    tenant = getattr(profile, 'tenant', None)
                else:
                    models.UserProfile.objects.create(
                        user=user,
                        tenant=tenant
                    )
                    
            except djangoexceptions.ObjectDoesNotExist:
                logger.debug(domain)
                
                userprofile = models.UserProfile(user=user,
                    tenant=tenant)
                
                setattr(user, 'userprofile', userprofile)
                
                userprofile.save()
            except:
                # If the profile lookup failed, we're in deep doodoo.  It's not 
                # safe to set a default tenant for this User - it might give access
                # to the base tenant which is cloned to create all new tenants.
                raise ValueError(
                    """A User was created with no profile.  For security reasons, 
                    we cannot allow the request to be processed any further.
                    Try deleting this User and creating it again to ensure a 
                    UserProfile gets attached, or link a UserProfile 
                    to this User.""")
        else:
            # It's important that we hit the db once to set the tenant, even if 
            # it's an anonymous user.  That way we get fresh values from the db,
            # including the tenant options.
            #
            # An anonymous user, for example, still has access to the login page,
            # so he will see the primary navigation tabs.  To decide which primary
            # navigation tabs to show, we need the tenant to be set.
            #
            # Not: If we simply set the tenant once and left it in a module-level 
            # variable, it would stay latched between page requests which is NOT
            # what we want.
            logging.info("default tenant")
            set_tenant_to_default()
