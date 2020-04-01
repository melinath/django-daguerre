Django Daguerre
===============

.. figure:: /_static/daguerre.png
   :alt: Louis-Jacques-Mandé Daguerre
   :align: right
   :scale: 33 %
   :target: http://en.wikipedia.org/wiki/Louis_Daguerre

   Louis Daguerre, Father of Photography

**Django Daguerre** manipulates images on the fly. Use it to scale
images up or down. Use it to generate thumbnails in bulk or sets of
responsive images without slowing down your templates. Or customize it
to do even more powerful image processing.

You don't need to run a cron job ahead of time. You don't need to make
any changes to your models. It **just works**.

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image "fill" width=200 height=400 %}" />

    {% adjust_bulk my_queryset "method.image" "fill" width=200 height=400 as adjusted_list %}
    {% for my_model, image in adjusted_list %}
      <img src="{{ image }}" />
    {% endfor %}


:Code:         http://github.com/melinath/django-daguerre
:Docs:         http://readthedocs.org/docs/django-daguerre/
:Build status: |build-image|

.. |build-image| image:: https://secure.travis-ci.org/melinath/django-daguerre.png?branch=master
                 :target: http://travis-ci.org/melinath/django-daguerre/branches

Contents
--------

.. toctree::
   :maxdepth: 2

   guides/installation-and-setup
   guides/template-tags
   guides/areas
   guides/commands
   guides/settings


API Docs
--------

.. toctree::
   :maxdepth: 2

   api/adjustments
   api/models


Release Notes
-------------

.. toctree::
   :maxdepth: 2

   release-notes/index


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

