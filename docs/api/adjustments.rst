Adjustments
===========

Daguerre provides a variety of adjustments to use when processing images, as well as an API for registering custom adjustments.

.. py:module:: daguerre.adjustments

.. autoclass:: Adjustment
    :members: parameters, calculate, adjust


Built-In Adjustments
--------------------

.. autoclass:: Fit
    :members: parameters
    :undoc-members:

.. autoclass:: Fill
    :members: parameters
    :undoc-members:

.. autoclass:: Crop
    :members: parameters
    :undoc-members:

.. autoclass:: RatioCrop
    :members: parameters
    :undoc-members:

.. autoclass:: NamedCrop
    :members: parameters
    :undoc-members:

When used with the template tag, these adjustments should be referred to by
their lowercase name:

.. code-block:: html+django

	{% adjust image "fit" width=300 %}

See :doc:`/guides/using-daguerre` for examples.

Custom Adjustments
------------------

You can easily add custom adjustments for your particular project. For
example, an adjustment to make an image grayscale might look
something like this:

.. code-block:: python

    # Somewhere that will be imported.
    from daguerre.adjustments import Adjustment, registry
    from PIL import ImageOps

    @registry.register
    class GrayScale(Adjustment):
        def adjust(self, image, areas=None):
            return ImageOps.grayscale(image)
        adjust.uses_areas = False

Now you can use your adjustment in templates:

.. code-block:: html+django

    {% adjust image "grayscale" %}
