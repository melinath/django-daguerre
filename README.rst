README
======

**Django Daguerre** makes it easy to adjust images on-the-fly without
slowing down your templates and without needing to generate everything
ahead of time with a cron job. You don't need to make any changes to
your models; it **Just Works**.

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image "fill" width=200 height=400 %}" />

    {% adjust_bulk my_queryset "method.image" "fill" width=200 height=400 as adjusted_list %}
    {% for my_model, image in adjusted_list %}
      <img src="{{ image }}" />
    {% endfor %}


:code:         http://github.com/littleweaver/django-daguerre
:docs:         http://readthedocs.org/docs/django-daguerre/
:build status: |build-image|

.. |build-image| image:: https://secure.travis-ci.org/littleweaver/django-daguerre.png?branch=master
                 :target: http://travis-ci.org/littleweaver/django-daguerre/branches

Requirements
------------

* Python 2.6+, 3.3+
* Pillow 2.3.0+
* Django 1.6+
* Six 1.5.2+

Daguerre *may* work with earlier versions of these packages, but they are not officially supported.

Upgrading from 1.0.X
--------------------

Daguerre 2.1 and up provide native Django migrations alongside
(new) South migrations. If you are migrating from Daguerre
1.0, and you have manually created data (for example Areas)
that you want to preserve, you *must* first upgrade to
Daguerre 2.0, run the migrations included in that version, and
*then* upgrade to Daguerre 2.1.

This migration path would look as follows::

    $ cd path/to/my/project
    $ pip install django-daguerre==2.0.0
    $ python manage.py migrate daguerre
    $ pip install -U django-daguerre
    $ python manage.py migrate daguerre 0001 --fake
    $ python manage.py migrate daguerre

If you *don't* have any manual data to preserve, and if it
would not adversely affect your site, you can also use the
following migration path::

    $ cd path/to/my/project
    $ python manage.py migrate daguerre zero # Or manually delete the daguerre tables
    $ pip install -U django-daguerre
    $ python manage.py migrate daguerre
    $ python manage.py daguerre clean

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    $ pip install django-daguerre

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

Using South
-----------

If you are using the South migrations (for example, if you
are on Django 1.6) you will need to add the following lines
to your settings::

    SOUTH_MIGRATION_MODULES = {
        'daguerre': 'daguerre.south_migrations',
    }

Testing
-------

We recommend running `tox`_ from the repository's root directory,
but you can also run ``test_project/manage.py test daguerre``.

.. _tox: http://tox.readthedocs.org/en/latest/
