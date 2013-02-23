Management commands
===================

``./manage.py clean_daguerre``
------------------------------

Cleans out extra data stored by daguerre:

* :class:`AdjustedImages <.AdjustedImage>` and :class:`Areas <.Area>` that reference storage paths which no longer exist.
* Duplicate :class:`AdjustedImages <.AdjustedImage>`.
* Adjusted image files which don't have an associated :class:`.AdjustedImage`.
