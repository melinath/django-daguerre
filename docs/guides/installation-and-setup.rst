Installation and Setup
======================

.. note::
   Daguerre 2.1 requires Python 2.7+ and Django 1.7+. For more information, see :ref:`versions-and-requirements`.

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

Now you're ready to :doc:`use Daguerre's template tags </guides/template-tags>`!

.. highlight:: bash

.. _upgrade-from-1.0:

Upgrading from 1.0.X
--------------------

Daguerre 2.1 and up use native Django migrations. If you are
migrating from Daguerre 1.0, and you have manually created
data (for example Areas) that you want to preserve, you
*must* first upgrade to Daguerre 2.0, run the migrations
included in that version, and *then* upgrade to Daguerre
2.1.

This migration path would look as follows::

    cd path/to/my/project
    pip install django-daguerre==2.0.0
    python manage.py migrate daguerre
    pip install -U django-daguerre
    python manage.py migrate daguerre 0001 --fake
    python manage.py migrate daguerre

If you *don't* have any manual data to preserve, and if it
would not adversely affect your site, you can also use the
following migration path::

    cd path/to/my/project
    python manage.py migrate daguerre zero # Or manually delete the daguerre tables
    pip install -U django-daguerre
    python manage.py migrate daguerre
    python manage.py daguerre clean

.. _versions-and-requirements:

Versions and Requirements
-------------------------

* Python 2.7+, 3.3+
* Pillow 2.3.0+
* Django 1.7+
* Six 1.5.2+

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
