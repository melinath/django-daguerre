Installation and Setup
======================

Requirements
------------

* Python 2.6+, 3.3+
* Pillow 2.3.0+
* Django 1.6+
* Six 1.3.0+

Daguerre *may* work with earlier versions of these packages, but it is untested.

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    pip install django-daguerre

You can clone the repository yourself at https://github.com/littleweaver/django-daguerre.

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