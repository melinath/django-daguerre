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


:code:         http://github.com/melinath/django-daguerre
:docs:         http://readthedocs.org/docs/django-daguerre/
:build status: |build-image|

.. |build-image| image:: https://secure.travis-ci.org/melinath/django-daguerre.png?branch=master
                 :target: http://travis-ci.org/melinath/django-daguerre/branches

Requirements
------------

* Python 2.7+, 3.5+
* Pillow
* Django 1.7 – 2.2
* Six 1.10.0+

Daguerre *may* work with earlier or later versions of these packages, but they are not officially supported.

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    $ pip install django-daguerre

You can clone the repository yourself at https://github.com/melinath/django-daguerre.


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

Run the migration command to create the database models::

    python manage.py migrate daguerre

Testing
-------

We recommend running `tox`_ from the repository's root directory,
but you can also run ``test_project/manage.py test daguerre``.

.. _tox: http://tox.readthedocs.org/en/latest/
