from django.conf import settings

BASE_TENANT_ID = getattr(settings, 'BASE_TENANT_ID', 1)
CREATE_MISSING_TENANT = getattr(settings, 'CREATE_MISSING_TENANT', False)