Template Tags
=============

.. highlight:: html+django

.. automodule:: daguerre.templatetags.daguerre
	:members: adjust

Daguerre comes with three built-in options for the ``adjustment`` parameter: ``crop``,
``fill``, and ``fit``. You can read more in :doc:`adjustments`.

.. note::
   
   The ``{% adjust %}`` tag handles images "lazily." The template tag
   generates a URI for the image, but the actual image processing is later
   handled by a view, only when the client hits the URI.

   In this way the image processing does not hold up template rendering. You
   can safely use multiple ``{% adjust %}`` tags for not-yet-processed images
   without impacting template rendering performance.

Examples
--------

The following examples assume that you are loading Daguerre's template
tag in your template::

	{% load daguerre %}

Scaling an image to fill a square space (the longer edge of the image will be
cropped)::

	<img src="{% adjust "path/to/image.png" adjustment="fill" width=200 height=200 %}" />

Fitting an image to a particular width and storing it as an :class:`AdjustmentInfoDict`::

	{% adjust "path/to/image.png" adjustment="fit" width=300 as image %}
	
	<img src="{{ image }}" width="{{ image.width }}" height="{{ image.height }}" />