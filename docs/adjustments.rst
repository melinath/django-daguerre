Adjustments
===========

Daguerre provides a variety of adjustments to use when processing images.

Built-In Adjustments
--------------------

.. highlight:: html+django

.. automodule:: daguerre.utils.adjustments
	:members: Crop, Fill, Fit

Examples
--------

When used with the template tag, these adjustments should be referred to by
their lowercase name::

	{% adjust adjustment="crop" height=200 width=200 %}

	{% adjust adjustment="fit" width=300 %}