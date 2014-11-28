from distutils.core import setup

# Ref: 
#     http://docs.python.org/distutils/setupscript.html#meta-data
#     http://pypi.python.org/pypi?%3Aaction=list_classifiers

from sys import version

setup(
    name='django-simple-multitenant',
    version='0.2.0',
    author='Daniel Romaniuk',
    author_email='daniel.romaniuk@gmail.com',
    packages=['multitenant',],
    url='https://github.com/phugoid/django-simple-multitenant',
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
