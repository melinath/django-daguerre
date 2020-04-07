Installation and Setup
======================

.. highlight:: bash

Installation
------------

Install the latest version of Daguerre using ``pip``::

    pip install django-daguerre

You can also clone the repository or download a package at
https://github.com/melinath/django-daguerre.

.. highlight:: python

Setup
-----

Add ``'daguerre'`` to your project's ``INSTALLED_APPS``::

   INSTALLED_APPS = (
       'daguerre',
       ...
   )

Add Daguerre's URL patterns to your URLconf::

   urlpatterns = patterns('',
       url(r'^daguerre/', include('daguerre.urls')),
       ...
   )

Run the migration command to create the database models::

    python manage.py migrate daguerre

Now you're ready to :doc:`use Daguerre's template tags </guides/template-tags>`!

.. _versions-and-requirements:

Versions and Requirements
-------------------------

* Python 3.5+
* Pillow
* Django 1.8 – 2.2
* Six 1.10.0+

Daguerre *may* work with earlier versions of these packages, but they
are not officially supported.
