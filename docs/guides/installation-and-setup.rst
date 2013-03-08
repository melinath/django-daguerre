Installation and Setup
======================

Requirements
------------

* Python 2.6+
* PIL 1.1.7 (Or `Pillow <http://pypi.python.org/pypi/Pillow>`_)

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