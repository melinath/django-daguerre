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

.. _template-tag-examples:

Examples
--------

The following examples assume that you are loading Daguerre's template
tag in your template::

	{% load daguerre %}

Scaling an image to fill a square space (the longer edge of the image will be
cropped)::

	<img src="{% adjust "path/to/image.png" adjustment="fill" width=200 height=200 %}" />


.. note::

   When using the template tag, :class:`.Crop` and :class:`.Fill` will
   automatically protect all :class:`.Area` instances that have been created
   on an image.

   You can create :class:`.Area` instances in the Django admin by editing an
   :class:`.Image` instance.

Fitting an image to a particular width and storing it as an :class:`AdjustmentInfoDict`::

	{% adjust "path/to/image.png" adjustment="fit" width=300 as image %}
	
	<img src="{{ image }}" width="{{ image.width }}" height="{{ image.height }}" />

Cropping an image to a particular pre-defined :class:`.Area`::

	<img src="{% adjust "path/to/image.png" adjustment="crop" crop="my-area-name" %}" />

	<img src="{% adjust "path/to/image.png" adjustment="fill" width=300 crop="my-area-name" %}" />
