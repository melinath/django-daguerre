Custom settings
===============

Adjust the image path
+++++++++++++++++++++

The variations are stored under a hashed directory path that starts with the
``dg`` directory by default (e.g. ``dg/ce/2b/7014c0bdbedea0e4f4bf.jpeg``).
This setting can be modified in the project's settings by setting the
``DAGUERRE_ADJUSTED_IMAGE_PATH`` variable.

Example:

.. code-block:: django

    # settings.py
    DAGUERRE_ADJUSTED_IMAGE_PATH = 'img'

which would produce the following path: ``img/ce/2b/7014c0bdbedea0e4f4bf.jpeg``


.. WARNING::
   The maximum length of the ``DAGUERRE_ADJUSTED_IMAGE_PATH`` string
   is 13 characters. If the string has more than 13 characters, it will
   gracefully fall back to the the default value, i.e. ``dg``
