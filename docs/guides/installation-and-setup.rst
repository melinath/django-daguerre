Installation and Setup
======================

Requirements
------------

* Python 2.6+, 3.3+
* Pillow 2.0.0+
* Django 1.4.5+
* Six 1.3.0+

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    pip install django-daguerre

You can clone the repository yourself at https://github.com/oberlin/django-daguerre.

.. highlight:: python

Setup
-----

Ensure that ``'daguerre'`` is in your project's ``INSTALLED_APPS``::

   INSTALLED_APPS = (
       'daguerre',
       ...
   )

Add the following or similar anywhere in your URLconf::

   urlpatterns = patterns('',
       url(r'^daguerre/', include('daguerre.urls')),
       ...
   )