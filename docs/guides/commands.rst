Management commands
===================

``./manage.py clean_daguerre``
------------------------------

Cleans out extra or invalid data stored by daguerre:

* :class:`AdjustedImages <.AdjustedImage>` and :class:`Areas <.Area>` that reference storage paths which no longer exist.
* Duplicate :class:`AdjustedImages <.AdjustedImage>`.
* Adjusted image files which don't have an associated :class:`.AdjustedImage`.
* :class:`.AdjustedImage` instances with missing adjusted image files.

``./manage.py preadjust [--remove]``
------------------------------------

Looks for a ``DAGUERRE_PREADJUSTMENTS`` setting using the following 
syntax::

    DAGUERRE_PREADJUSTMENTS = {
        ('myapp.MyModel', 'template.style.lookup'): (
            {'adjustment': 'fit',
             'width': 800,
             'height': 500},
            {'adjustment': 'fill',
             'width': 300,
             'height': 216},
            ...
        ),
    }

In this dictionary, the values are lists of adjustment keyword
arguments. The keys are tuples where the first value is either an 
``'<applabel>.<ModelName>'`` string, a model class, or a queryset, and 
the second value is a template-style lookup which can be applied to each 
item of the given model type in order to get an ``ImageFieldFile`` or a 
storage path.

The command will collect storage paths based on the keys and make
:class:`AdjustedImages <.AdjustedImage>` for each one based on the list of kwargs, if such an :class:`.AdjustedImage` doesn't already exist.

If ``--remove`` is specified, the command will delete all :class:`.AdjustedImage` 
instances which do not match one of the model/lookup/kwargs combinations 
specified in ``DAGUERRE_PREADJUSTMENTS``.
