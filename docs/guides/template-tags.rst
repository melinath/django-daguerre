Template Tags
=============

.. module:: daguerre.templatetags.daguerre

.. templatetag:: {% adjust %}

adjust
++++++

The easiest way to use Daguerre is through the :ttag:`{% adjust %}`
template tag:

.. code-block:: html+django

    {% load daguerre %}
    <img src="{% adjust my_model.image 'fill' width=128 height=256 %}" />

The :ttag:`{% adjust %}` tag works directly with any ImageField (or storage path).
There is no magic. You don't need to change your models. It Just Works.

Daguerre provides a number of built-in adjustments (such as 'fill') which
can be used with the :ttag:`{% adjust %}` out of the box, as well as an
API for registering custom adjustments.

Take this picture:

.. figure:: /_static/cat.jpg

    Full size: 800x600. This photograph, by Wikipedia user `Sloesch <http://de.wikipedia.org/wiki/Benutzer:Sloesch>`_,
    is licensed as `CC BY-SA <http://creativecommons.org/licenses/by-sa/3.0/>`_.

Let's use :ttag:`{% adjust %}` with width 200 (25%) and height 300
(50%), with three of the built-in adjustments.

+-----------------------------------+------------------------------------+------------------------------------+
| "fit"                             | "fill"                             | "crop"                             |
+===================================+====================================+====================================+
| .. image:: /_static/cat_fit.jpg   | .. image:: /_static/cat_fill.jpg   | .. image:: /_static/cat_crop.jpg   |
+-----------------------------------+------------------------------------+------------------------------------+
| Fits the entire image into the    | Fills the entire space given by    | Crops the image to the given       |
| given dimensions without          | the dimensions by cropping to the  | dimensions without any resizing.   |
| distorting it.                    | same width/height ratio and then   |                                    |
|                                   | scaling down or up.                |                                    |
+-----------------------------------+------------------------------------+------------------------------------+

Chaining Adjustments
--------------------

You can also use the :ttag:`{% adjust %}` tag to chain multiple
adjustments. Take the following:

.. code-block:: html+django

    {% load daguerre %}
    {% adjust my_model.image 'ratiocrop' ratio='16:9' 'fit' width=200 %}

This tag first crops the image to a 16:9 ratio, then scales as much as
needed to fit within a 200-pixel width. In other words:

.. image:: /_static/cat_ratiocrop_fit.jpg

.. seealso:: :mod:`daguerre.adjustments` for more built-in adjustments.

Getting adjusted width and height
---------------------------------

.. code-block:: html+django

    {% load daguerre %}
    {% adjust my_model.image 'fit' width=128 height=128 as image %}
    <img src="{{ image }}" width="{{ image.width }}" height="{{ image.height }}" />

The object being set to the ``image`` context variable is an
:class:`.AdjustmentInfoDict` instance. In addition to rendering as
the URL for an image, this object provides access to some other
useful pieces of information—in particular, the width and height
that the adjusted image *will have*, based on the width and height
of the original image and the parameters given to the tag. This can
help you avoid changes to page flow as adjusted images load.

Let's be lazy
-------------

So the :ttag:`{% adjust %}` tag renders as a URL to adjusted image,
right? Yes, but as lazily as possible. If the adjustment has already
been performed, the adjusted image's URL is fetched from the database.
If the adjustment has *not* been performed, the tag renders as a URL
to a view which, when accessed, will create an adjusted version of the
image and return a redirect to the adjusted image's actual URL.

This does have the downside of requiring an additional
request/response cycle when unadjusted images are fetched by the user
– but it has the upside that no matter how many :ttag:`{% adjust %}`
tags you have on a page, the initial load of the page won't be slowed
down by (potentially numerous, potentially expensive) image
adjustments.

.. note::

    The adjustment view has some light security in place to
    make sure that users can't run arbitrary image resizes on your
    servers.


.. templatetag:: {% adjust_bulk %}

adjust_bulk
+++++++++++

If you are using a large number of similar adjustments in one
template - say, looping over a queryset and adjusting the same
attribute each time - you can save yourself queries by using
:ttag:`{% adjust_bulk %}`.

.. code-block:: html+django

    {% load daguerre %}
    {% adjust_bulk my_queryset "method.image" "fill" width=200 height=400 as adjusted_list %}
    {% for my_model, image in adjusted_list %}
      <img src="{{ image }}" />
    {% endfor %}

The syntax is similar to :ttag:`{% adjust %}`, except that:

* ``as <varname>`` is required.
* an iterable (``my_queryset``) and a lookup to be performed on each
  item in the iterable (``"method.image"``) are provided in place
  of an image file or storage path. (If the iterable is an iterable of
  image files or storage paths, the lookup is not required.)

You've got everything you need now to use Daguerre and resize images
like a champ. But what if you need more control over *how* your images
are cropped? Read on to learn about :doc:`/guides/areas`.