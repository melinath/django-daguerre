Django Daguerre
===============

.. figure:: /_static/daguerre.png
   :alt: Louis-Jacques-Mandé Daguerre
   :align: right
   :scale: 33%
   :target: http://en.wikipedia.org/wiki/Louis_Daguerre
   
   Louis Daguerre, Father of Photography

**Django Daguerre** makes it easy to adjust images on-the-fly without
slowing down your templates and without needing to generate everything
ahead of time with a cron job. You don't need to make any changes to
your models; it **Just Works**.

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image width=200 height=400 %}" />

    {% adjust_bulk my_queryset "image" width=200 height=400 as adjusted_dict %}
    {% for my_model, image in adjusted_dict.iteritems %}
      <img src="{{ image }}" />
    {% endfor %}

Contents
--------

.. toctree::
   :maxdepth: 2

   guides/installation-and-setup
   guides/using-daguerre
   project


API Docs
--------

.. toctree::
   :maxdepth: 2

   api/adjustments
   api/models


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

