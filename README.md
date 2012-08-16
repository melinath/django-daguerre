Django Daguerre
===============

**Django Daguerre** makes it easy to adjust images on-the-fly without
slowing down your templates and without needing to generate everything
ahead of time with a cron job. You don't need to make any changes to
your models; it **Just Works**.

Requirements
------------

* Python 2.5+
* PIL 1.1.7 (Or [Pillow](http://pypi.python.org/pypi/Pillow))

Installation
------------

You can install the latest version of Daguerre using `pip`:

    pip install git+https://github.com/oberlin/django-daguerre.git@master#egg=daguerre

Setup
-----

Ensure that `'daguerre'` is in your project's `INSTALLED_APPS`:

    INSTALLED_APPS = (
        'daguerre',
        ...
    )

Add the following or similar anywhere in your URLconf:

    urlpatterns = patterns('',
        url(r'^daguerre/', include('daguerre.urls')),
        ...
    )