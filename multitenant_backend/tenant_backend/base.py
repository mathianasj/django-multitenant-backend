#import re
#import warnings
from django.conf import settings
from types import MethodType
from threadlocals.threadlocals import get_current_request

try:
    # Django versions >= 1.9
    from django.utils.module_loading import import_module
except ImportError:
    # Django versions < 1.9
    from django.utils.importlib import import_module

ORIGINAL_BACKEND = getattr(settings, 'ORIGINAL_BACKEND', 'django.db.backends.postgresql_psycopg2')

original_backend = import_module(ORIGINAL_BACKEND + '.base')

class DatabaseWrapper(original_backend.DatabaseWrapper):
    """
    Adds the capability to manipulate the search_path using set_tenant and set_schema_name
    """
    include_public_schema = True

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        
        self.set_schema_to_public()

    def close(self):
        self.search_path_set = False
        super(DatabaseWrapper, self).close()

    def rollback(self):
        super(DatabaseWrapper, self).rollback()
        # Django's rollback clears the search path so we have to set it again the next time.
        self.search_path_set = False

    def set_tenant(self, tenant, include_public=True):
        """
        Main API method to current database schema,
        but it does not actually modify the db connection.
        """
        print("setting tenant in connection to {}".format(tenant))
        self.tenant = tenant

    def set_schema_to_public(self):
        """
        Instructs to stay in the common 'public' schema.
        """
        print('setting schema to public')
        self.tenant = DefaultTenant()

    def _cursor(self):
        """
        Here it happens. We hope every Django db operation using PostgreSQL
        must go through this to get the cursor handle. We change the path.
        """
        cursor = super(DatabaseWrapper, self)._cursor()

        # optionally limit the number of executions - under load, the execution
        # of `set search_path` can be quite time consuming
        # Actual search_path modification for the cursor. Database will
        # search schemata from left to right when looking for the object
        # (table, index, sequence, etc.).
        if not self.tenant:
            raise ImproperlyConfigured("Tenant is not defined. Did you forget "
                                        "to call set_schema() or set_tenant()?")
        
        # In the event that an error already happened in this transaction and we are going
        # to rollback we should just ignore database error when setting the search_path
        # if the next instruction is not a rollback it will just fail also, so
        # we do not have to worry that it's not the good one
        try:
            if(ORIGINAL_BACKEND == 'django.db.backends.mysql'):
                orig = cursor.execute
                tenant = self.tenant
                def new_exec(self, query, args=None):
                    print('override sql {}'.format(query))
                    if tenant:
                        print("current tenant id: {}".format(tenant.id))
                        if(args):
                            print("about to replace {{tenant_id}}")
                            mut_args = []
                            for x in args:
                                if(x == '{{tenant_id}}'):
                                    mut_args.append(tenant.id)
                                else:
                                    mut_args.append(x)
                            
                            print(args)
                            print(mut_args)
                            args = tuple(mut_args)
                    
                    return orig(query, args)
                cursor.execute = MethodType(new_exec, cursor)
            else:
                cursor.execute('SET search_path = {0}'.format(','.join(search_paths)))
        except (django.db.utils.DatabaseError, psycopg2.InternalError):
            self.search_path_set = False
        else:
            self.search_path_set = True
            
        return cursor


class DefaultTenant:
    id=1

if ORIGINAL_BACKEND == "django.contrib.gis.db.backends.postgis":
    DatabaseError = django.db.utils.DatabaseError
    IntegrityError = psycopg2.IntegrityError
else:
    DatabaseError = original_backend.DatabaseError
    IntegrityError = original_backend.IntegrityError
