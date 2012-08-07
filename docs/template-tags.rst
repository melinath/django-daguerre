Template Tags
=============

.. automodule:: daguerre.templatetags.daguerre
	:members: adjust

Daguerre comes with three built-in options for the ``adjustment`` parameter: ``crop``,
``fill``, and ``fit``. You can read more in :doc:`adjustments`.

.. highlight:: html+django

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