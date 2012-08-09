Using daguerre
==============

.. module:: daguerre.templatetags.daguerre

.. templatetag:: {% adjust %}

{% adjust %}
++++++++++++

The easiest way to use Daguerre is through the :ttag:`{% adjust %}`
template tag:

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image.name width=128 height=256 %}" />

:mod:`daguerre` works directly with image storage paths. There is no
magic. You don't need to change your models. It Just Works.

Let's be lazy
-------------

So the :ttag:`{% adjust %}` tag renders as a URL which gets an
adjusted image, right? Well, yes, but in a very lazy fashion. It
actually renders a URL to an adjustment view, which runs the
adjustment (if necessary) and then redirects the user to the actual
adjusted image's URL.

The upshot of this is that no matter how many :ttag:`{% adjust %}`
tags you have on a page, it will render as quickly when the
thumbnails already exist as it will when the thumbnails still need
to be created. The thumbnails will then be filled in as the user
starts to request them.

.. note::

    The adjustment view has some light security in place to
    make sure that users can't run arbitrary image resizes on your
    servers.

Different adjustments
---------------------

The :ttag:`{% adjust %}` tag currently supports three different
adjustments: **fit, fill, and crop.** These can be passed in as an
additional parameter to the tag:

.. code-block:: html+django

    <img src="{% adjust my_model.image.name width=128 height=256 adjustment="fit" %}" />

Take this picture:

.. figure:: /_static/lenna.png

    Full size: 512x512

Let's use :ttag:`{% adjust %}` with width 128 (25%) and height 256
(50%), with each of the three adjustments.

+-----------------------------------+------------------------------------+------------------------------------+
| "fit"                             | "fill" (default)                   | "crop"                             |
+===================================+====================================+====================================+
| .. image:: /_static/lenna_fit.png | .. image:: /_static/lenna_fill.png | .. image:: /_static/lenna_crop.png |
+-----------------------------------+------------------------------------+------------------------------------+
| Fits the entire image into the    | Fills the entire space given by    | Crops the image to the given       |
| given dimensions without          | the dimensions by cropping to the  | dimensions without any resizing.   |
| distorting it.                    | same width/height ratio and then   |                                    |
|                                   | scaling.                           |                                    |
+-----------------------------------+------------------------------------+------------------------------------+

.. note::

    If you have defined :class:`.Area`\ s for an image in the admin,
    those will be protected as much as possible (according to their
    priority) when using the crop or fill adjustments. Otherwise,
    any cropping will be done evenly from opposing sides.

Getting adjusted width and height
---------------------------------

.. code-block:: html+django

    {% load daguerre %}
    {% adjust my_model.image.name width=128 height=128 adjustment="fit" as image %}
    <img src="{{ image }}" width={{ image.width }} height={{ image.height }} />

The object being set to the ``image`` context variable is an
:class:`.AdjustmentInfoDict` instance. In addition to rendering as
the URL for an image, this object provides access to some other
useful pieces of information - in particular, the width and height
that the adjusted image *will have*, based on the width and height
of the original image and the parameters given to the tag. This can
help you avoid changes to page flow as adjusted images load.

Named crops (advanced)
----------------------

If you are defining :class:`.Area`\ s in the admin, you can refer to
these by name to pre-crop images **before** applying the adjustment
you've selected. For example:

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image.name width=128 height=128 adjustment="fit" crop="face" %}" />

This would first crop the image to the "face" :class:`.Area` (if available)
and then fit that cropped image into a 128x128 box.

.. note::

    If a named crop is being used, :class:`.Area`\ s will be
    ignored even if you're using a fill or crop adjustment. (This may
    change in the future.)
