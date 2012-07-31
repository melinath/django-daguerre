Getting Started
===============

Installation
------------

You can install the latest version of Daguerre with `pip install git+https://github.com/oberlin/django-daguerre.git@master#egg=daguerre`.

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