from distutils.core import setup

# Ref: 
#     http://docs.python.org/distutils/setupscript.html#meta-data
#     http://pypi.python.org/pypi?%3Aaction=list_classifiers

from sys import version

setup(
    name='django-multitenant-backend',
    version='0.3.0',
    author='Joshua Mathianas',
    author_email='mathianasj@gmail.com',
    packages=['multitenant_backend',],
    url='https://github.com/mathianasj/django-multitenant-backend',
    license='LICENSE.txt',
    description='Helps manage multi tenancy for django projects',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Utilities',
    ],
)
