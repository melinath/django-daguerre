Adjustments
===========

Daguerre provides a variety of adjustments to use when processing images.

Built-In Adjustments
--------------------

.. highlight:: html+django

.. py:module:: daguerre.utils.adjustments

.. autoclass:: Crop

.. autoclass:: Fill

.. autoclass:: Fit

When used with the template tag, these adjustments should be referred to by
their lowercase name::

	{% adjust adjustment="fit" width=300 %}

See :doc:`/guides/using-daguerre` for examples.