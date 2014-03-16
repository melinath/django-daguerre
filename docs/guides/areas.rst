Smart Cropping With Areas
=========================

Daguerre provides a widget which can be used with any
:class:`ImageField` to edit :class:`Areas <.Area>` for that image file.
Using this widget with a :class:`ModelAdmin` is as simple as defining
appropriate `formfield_overrides`_.

.. code-block:: python

    from daguerre.widgets import AreaWidget

    class YourModelAdmin(admin.ModelAdmin):
        formfield_overrides = {
            models.ImageField: {'widget': AreaWidget},
        }
        ...

After you define :class:`Areas <.Area>` for an image in the admin,
adjustments that remove parts of the image (such as crop and fill) can
take them into account and protect those parts of the image during
processing. Otherwise, any cropping will be done evenly from opposing
sides.

.. _formfield_overrides: https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.formfield_overrides
