Installation and Setup
======================

Requirements
------------

* Python 2.5+
* PIL 1.1.7 (Or `Pillow <http://pypi.python.org/pypi/Pillow>`_)
* django-grappelli (for the admin)

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    pip install git+https://github.com/oberlin/django-daguerre.git@master#egg=daguerre

You can clone the repository yourself at https://github.com/oberlin/django-daguerre.

.. highlight:: python

Setup
-----

Ensure that these are in your project's ``INSTALLED_APPS``::

   INSTALLED_APPS = (
       'grappelli', # must appear before 'django.contrib.admin'
       'daguerre', # may appear anywhere in the list
       ...
   )

Add the following or similar anywhere in your URLconf::

   urlpatterns = patterns('',
       url(r'^grappelli/', include('grappelli.urls')),
       url(r'^daguerre/', include('daguerre.urls')),
       ...
   )