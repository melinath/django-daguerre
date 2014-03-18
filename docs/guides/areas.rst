Smart Cropping with Areas
=========================

Daguerre allows you to influence how images are cropped with
:class:`Areas <.Area>`.

Use the AreaWidget
------------------

Daguerre provides a widget which can be used with any
:class:`ImageField` to edit :class:`Areas <.Area>` for that image file.
Add this `formfield override <formfield_override>`_ to your ModelAdmin to enable the widget.

.. code-block:: python

    from daguerre.widgets import AreaWidget

    class YourModelAdmin(admin.ModelAdmin):
        formfield_overrides = {
            models.ImageField: {'widget': AreaWidget},
        }
        ...

.. figure:: /_static/areawidget.png
   :alt: Screenshot of the Area Widget in the admin.

   The :class:`AreaWidget` allows you to define areas of an image with
   click-and-drag. (Screenshot includes `Grappelli`_.)

Adjustments with Areas
----------------------

After you define :class:`Areas <.Area>` for an image in the admin,
adjustments that remove parts of the image (such as crop) will protect
those parts of the image during processing. See the difference in this
adjustment.

.. code-block:: html+django

	<img src="{% adjust my_model.image "fill" width=600 height=200 %}" />

+--------------------------------------------------+
| Result without 'face' Area defined               |
+==================================================+
| .. image:: /_static/cat_face_not_protected.jpg   |
+--------------------------------------------------+

+----------------------------------------------+
| Result with 'face' Area defined              |
+==============================================+
| .. image:: /_static/cat_face_protected.jpg   |
+----------------------------------------------+

Areas and namedcrop
-------------------

You can also use the built-in "namedcrop" adjustment force a specific crop.

.. code-block:: html+django

	<img src="{% adjust my_model.image "namedcrop" area="face" %}" />

.. image:: /_static/cat_named_crop.jpg

.. _formfield_override: https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.formfield_overrides
.. _Grappelli: http://grappelliproject.com/