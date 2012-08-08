Getting Started
===============

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    pip install git+https://github.com/oberlin/django-daguerre.git@master#egg=daguerre

You can clone the repository yourself at https://github.com/oberlin/django-daguerre.

.. highlight:: python

Setup
-----

Ensure that these are in your project's `INSTALLED_APPS`::

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

.. highlight:: html+django

Usage
-----

The easiest way to use Daguerre is through the ``{% adjust %}`` template tag::

	{% adjust "storage/path/to/image.png" adjustment="fit" width=600 height=800 %}

Read more in :doc:`template-tags`.