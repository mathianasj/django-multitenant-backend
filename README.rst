Multitenancy is a way to support multiple isolated clients or tenants with a shared server deployment. See http://en.wikipedia.org/wiki/Multitenancy for details and a good introduction on multitenancy approaches: http://msdn.microsoft.com/en-us/library/aa479086.aspx 

This Django app implements the shared approach: partitionionig data using a tenant key in each table. It helps manage multitenancy.  Your web application can have several tenants, each with several users.  The users from one tenant are not allowed to see the data (model instances) that belong to another tenant.

Note: I have adapted this version from https://github.com/pombredanne/django-simple-multitenant to support the latest version python and django.  The creation of a backend wrapper around mysql db backend enables the use of direct sql modifictions for the tenant id when using 
lazy fetch and serilization with django rest framework.  There is no longer a need to modify any existing code to implement a shared database key multitenancy.  It would be best to partition your database tables based on the tenant ids to help segment the data.

That said, partitioning here is done at the database table (django model) level.  At the core is a model called Tenant, with only two fields: 
name and email.  Any other model in your django project can be made "tenant-aware" by adding a ForeignKey field pointed at 
that Tenant model. django-simple-multitenant helps reduce the amount of boilerplate code you need to make your models tenant-aware.

How to use
==========

Models
------
To make a tenant-aware model, simply subclass django-multitenant's TenantModel.
example::

	from django.db import models
	from multitenant.models import TenantModel

	class BugReport(TenantModel)
		description = models.CharField(max_length=200)

TenantModels have a tenant-aware manager called tenant_objects::

	bugs = BugReport.tenant_objects.all()

This will bring up all instances owned by the "current tenant".
The current tenant, for a given request, is determined by checking the tenant field of the user profile for request.user.
If it's an anonymous user, the current tenant will be the base tenant.  
See the base tenant section below for more information.


Forms
-----
For any model that subclasses TenantModel, you'll want to use a TenantModelForm instead of django's ModelForm.
The TenantModelForm has two useful features:

1. All ModelChoiceFields and ModelMultipleChoiceFields have their querysets filtered to show only the values for the current tenant.
   This happens during form class instantiation.
2. The form's clean() method sets the instance's tenant field to that of the currently logged in user.

example::

	class CompanyForm(TenantModelForm):
	    class Meta:
	        model = Company
	        exclude = ['tenant']

Note that we don't need to worry about filtering the options available for each form field.  You should exclude the tenant form field
as above, not out of security concerns but rather to avoid complications while cleaning the form.
	

Admin
-----
By default, django-admin will show you all model instances.  In a multitenant project, you might want to 
"visit" a tenant's account, and see just the instances that belong to them.  If you use TenantAdmin as your
ModelAdmin class, you will see only the instances for the currently logged-in user (yourself).

You can then visit any tenant you please, by changing the Tenant linked to your own user profile.

example::

	from django.contrib import admin
	from multitenant.admin import TenantAdmin
	from myapp.models import *
	
	admin.site.register(BugReport, TenantAdmin)    

Utilities
---------
To verify that the current logged in tenant owns a particular instance::

	from multitenant.utils import current_tenant_owns_object

	if current_tenant_owns_object(obj):
		do_something()

A tenant-aware version of django's get_object_or_404 shortcut::

	from multitenant.utils import tenant_get_object_or_404

	tenant_get_object_or_404(BugReport, id=1)

To filter a queryset so that all instances belong to the currently logged in tenant::

	from multitenant.utils import tenant_filter
	
	bugs = BugReport.objects.all()
	bugs = tenant_filter(bugs)

To get the Tenant instance for the currently logged in tenant::

	from multitenant.middleware import get_current_tenant

	tenant = get_current_tenant()

In very rare instances, such as in django management commands, you might need to set the current tenant manually
as there is no logged in user::

	from multitenant.middleware import set_current_tenant, set_tenant_to_default

	if val:
		set_current_tenant( Tenant.objects.get(id=val) )
	else:
		set_tenant_to_default()
	

Installation and Setup
======================

Django apps
-----------
Add django-multitenant to your list of installed apps:
example::

	INSTALLED_APPS = (
	    'django.contrib.auth',
	    'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'django.contrib.sites',
	    'django.contrib.messages',
	    'django.contrib.staticfiles',
	    'multitenant',
    )	
	
Middleware
----------
To have the tenant set automatically, add the middleware straight after
`django.contrib.auth.middleware.AuthenticationMiddleware`.
example::

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'multitenant.middleware.ThreadLocals',
        ...
    )

**WARNING**
The middleware uses threadlocals which isn't universally considered a good idea.


User Profile
------------
You must have a "user profile" model, and it must subclass TenantModel. 
This is the django model that you use to extend auth.User, the one pointed to by AUTH_PROFILE_MODULE in your settings.py file; for a
complete discussion see https://docs.djangoproject.com/en/dev/topics/auth/#storing-additional-information-about-users

example::

	class UserProfile(TenantModel):
	    user = models.OneToOneField(User)

Base tenant
-----------
The first tenant (id=1) is called the "base tenant", and should be read-only.  It is not used by regular users.
This is where you set up all the tenant-aware model instances for a new, empty tenant account.  Now, when you create a new tenant, say with id=2,
this clones all the instances from the base tenant.

example, say you have a model called BugReportType.  You may want each tenant to have their own set of custom BugReportTypes.  When you
first create a tenant, they need a decent set of values to start with.
Set up a few starting values, for the base tenant (id=1)::

	mysql> select * from multitenant_tenant;
	+----+-------------------------+---------------------+
	| id | name                    | email               |
	+----+-------------------------+---------------------+
	|  1 | Base tenant (read-only) | example@example.com |
	+----+-------------------------+---------------------+
		
	mysql> select * from bugs_bugreporttype;
	+-----+-----------+---------+
	| id  | tenant_id | name    | 
	+-----+-----------+---------+
	|   1 |         1 | Closed  |
	|   2 |         1 | In Work |
	+-----+-----------+---------+

What happens when we create a new tenant?  The base tenant gets cloned::

	mysql> select * from multitenant_tenant;
	+----+-------------------------+---------------------+
	| id | name                    | email               |
	+----+-------------------------+---------------------+
	|  1 | Base tenant (read-only) | example@example.com |
	|  1 | Acme                    | example@acme        |
	+----+-------------------------+---------------------+
		
	mysql> select * from bugs_bugreporttype;
	+-----+-----------+---------+
	| id  | tenant_id | name    | 
	+-----+-----------+---------+
	|   1 |         1 | Closed  |
	|   2 |         1 | In Work |
	|   3 |         2 | Closed  |
	|   4 |         2 | In Work |
	+-----+-----------+---------+

So you should set up a base tenant with a starting set of values for all the tenant-aware models in your project.


Special Considerations and Warnings
===================================
Uniqueness constraints
----------------------
Add the tenant field to any uniqueness constraints for tenant-aware models; 
remember that more than one tenant is now sharing the same database table.
example::

	unique_together = (("name", "tenant"), ("code", "tenant"),)

Default values
--------------
Be careful with default values for ForeignKey or model fields.  You don't want the default 

bad example::

	class BugReport(TenantModel)
	    bug_type = models.ForeignKey(
	        BugReportType, 
	        on_delete = models.SET_DEFAULT,
	        default = BugReportType.tenant_objects.get(name='New')
	    )

That's a bad example because it depends on the current tenant being known while the BugReport
class is declared.  It's far better to use a callable (function) as default value.

better example::

	class BugReport(TenantModel)
	    bug_type = models.ForeignKey(
	        BugReportType, 
	        on_delete = models.SET_DEFAULT,
	        default = get_default_bugreporttype
	    )
			
    def get_default_bugreporttype():
        return BugReportType.tenant_objects.get(name='New')

Difficulty with bootstrapping the database
------------------------------------------
When you first run syncdb with the multitenant app installed, you may run into a chicken-and-egg problem with the user profile model class.  
The user profile model must subclass TenantModel; it has a foreign key relation to Tenant.  To create a new user profile, you must first create
a Tenant instance.


License
-------
django-multitenant, a tool to help manage multitenancy for django projects
Copyright (C) 2011, Daniel Romaniuk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
