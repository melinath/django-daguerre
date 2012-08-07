Adjustments
===========

.. highlight:: html+django

Daguerre includes several built-in adjustment methods that can be used for
processing images.

.. automodule:: daguerre.utils.adjustments
	:members: Crop, Fill, Fit

When used with the template tag, these adjustments should be referred to by
their lowercase name::

	{% adjust adjustment="crop" height=200 width=200 %}

	{% adjust adjustment="fit" width=300 %}