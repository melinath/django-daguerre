Getting Started
===============

Installation
------------

You can install the latest version of Daguerre using ``pip``::

    pip install git+https://github.com/oberlin/django-daguerre.git@master#egg=daguerre

You can clone the repository yourself at https://github.com/oberlin/django-daguerre.

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