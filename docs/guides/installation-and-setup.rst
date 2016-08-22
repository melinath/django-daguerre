Installation and Setup
======================

.. highlight:: bash

Installation
------------

Install the latest version of Daguerre using ``pip``::

    pip install django-daguerre

You can also clone the repository or download a package at
https://github.com/littleweaver/django-daguerre.

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

* Python 2.7+, 3.3+
* Pillow
* Django 1.7, 1.8 & 1.9
* Six 1.10.0+

Daguerre *may* work with earlier versions of these packages, but they
are not officially supported.

If you need to use earlier versions of Python or Django, refer this
versions table to determine which version of Daguerre to install.

=============== =================== ===============
Package         Python              Django
=============== =================== ===============
Daguerre 2.1.0  Python 2.7+, 3.3+   Django 1.7+  
Daguerre 2.0.0  Python 2.6+, 3.3+   Django 1.6.1+
Daguerre 1.0.1  Python 2.6+         Django 1.4+
=============== =================== ===============

You can install older versions of Daguerre with pip. E.g.,

.. code-block:: bash

   pip install django-daguerre==2.0
