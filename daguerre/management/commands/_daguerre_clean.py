from __future__ import absolute_import
import os

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import models
from django.template.defaultfilters import pluralize
import six

from daguerre.helpers import IOERRORS
from daguerre.models import AdjustedImage, Area


class Command(BaseCommand):
    def _delete_queryset(
            self,
            queryset,
            reason='reference nonexistant paths',
            reason_plural=None):
        count = queryset.count()
        if count == 1:
            name = six.text_type(queryset.model._meta.verbose_name)
            reason = reason
        else:
            name = six.text_type(queryset.model._meta.verbose_name_plural)
            reason = reason_plural or reason
        if count == 0:
            self.stdout.write(u"No {0} {1}.\n".format(name, reason))
        else:
            self.stdout.write(u"Deleting {0} {1} which {2}... ".format(
                count, name, reason))
            self.stdout.flush()
            queryset.delete()
            self.stdout.write("Done.\n")

    def _walk(self, dirpath, topdown=True):
        """
        Recursively walks the dir with default_storage.
        Yields (dirpath, dirnames, filenames) tuples.
        """
        try:
            dirnames, filenames = default_storage.listdir(dirpath)
        except (NotImplementedError, OSError):
            # default_storage can't listdir, or dir doesn't exist
            # (local filesystem.)
            dirnames, filenames = [], []

        if topdown:
            yield dirpath, dirnames, filenames

        for dirname in dirnames:
            for value in self._walk(os.path.join(dirpath, dirname), topdown):
                yield value

        if not topdown:
            yield dirpath, dirnames, filenames

    def _old_adjustments(self):
        """
        Returns a queryset of AdjustedImages whose storage_paths no longer
        exist in storage.

        """
        paths = AdjustedImage.objects.values_list(
            'storage_path', flat=True).distinct()
        missing = [
            path for path in paths
            if not default_storage.exists(path)
        ]
        return AdjustedImage.objects.filter(storage_path__in=missing)

    def _old_areas(self):
        """
        Returns a queryset of Areas whose storage_paths no longer exist in
        storage.

        """
        paths = Area.objects.values_list(
            'storage_path', flat=True).distinct()
        missing = [
            path for path in paths
            if not default_storage.exists(path)
        ]
        return Area.objects.filter(storage_path__in=missing)

    def _missing_adjustments(self):
        """
        Returns a queryset of AdjustedImages whose adjusted image files no
        longer exist in storage.

        """
        paths = AdjustedImage.objects.values_list(
            'adjusted', flat=True).distinct()
        missing = [
            path for path in paths
            if not default_storage.exists(path)
        ]
        return AdjustedImage.objects.filter(adjusted__in=missing)

    def _duplicate_adjustments(self):
        """
        Returns a queryset of AdjustedImages which are duplicates - i.e. have
        the same requested adjustment and storage path as another
        AdjustedImage. This excludes one adjusted image as the canonical
        version.

        """
        fields = (
            'storage_path',
            'requested'
        )
        kwargs_list = AdjustedImage.objects.values(
            *fields).annotate(
                count=models.Count('id')).filter(
                    count__gt=1).values(
                        *fields)
        duplicate_pks = []
        for kwargs in kwargs_list:
            pks = AdjustedImage.objects.filter(
                **kwargs).values_list('pk', flat=True)
            duplicate_pks.extend(list(pks)[1:])
        return AdjustedImage.objects.filter(pk__in=duplicate_pks)

    def _orphaned_files(self):
        """
        Returns a list of files which aren't referenced by any adjusted images
        in the database.

        """
        known_paths = set(
            AdjustedImage.objects.values_list('adjusted', flat=True).distinct()
        )
        orphans = []
        for dirpath, dirnames, filenames in self._walk(
                'daguerre', topdown=False):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if filepath not in known_paths:
                    orphans.append(filepath)
        return orphans

    def handle(self, **options):
        # Clear all adjusted images that reference nonexistant
        # storage paths.
        self._delete_queryset(self._old_adjustments())

        # Clear all areas that reference nonexistant storage paths.
        self._delete_queryset(self._old_areas())

        # Clear all adjusted images that reference nonexistant adjustments.
        self._delete_queryset(self._missing_adjustments(),
                              'reference missing adjustments')

        # Clear all duplicate adjusted images.
        self._delete_queryset(self._duplicate_adjustments(),
                              reason='is a duplicate',
                              reason_plural='are duplicates')

        # Clean up files that aren't referenced by any adjusted images.
        orphans = self._orphaned_files()
        if not orphans:
            self.stdout.write("No orphaned files found.\n")
        else:
            self.stdout.write(
                "Deleting {0} orphaned file{1}... ".format(
                    len(orphans),
                    pluralize(len(orphans))))
            self.stdout.flush()
            for filepath in orphans:
                try:
                    default_storage.delete(filepath)
                except IOERRORS:
                    pass
            self.stdout.write("Done.\n")

        self.stdout.write("\n")
