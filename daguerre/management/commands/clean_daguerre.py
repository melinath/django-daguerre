import os

from django.core.files.storage import default_storage
from django.core.management.base import NoArgsCommand
from django.db import models
from django.template.defaultfilters import pluralize

from daguerre.models import AdjustedImage, Area


class Command(NoArgsCommand):
	def _delete_queryset(self, queryset, reason='reference nonexistant paths', reason_plural=None):
		count = queryset.count()
		if count == 1:
			name = unicode(queryset.model._meta.verbose_name)
			reason = reason
		else:
			name = unicode(queryset.model._meta.verbose_name_plural)
			reason = reason_plural or reason
		if count == 0:
			self.stdout.write(u"No {0} {1}.\n".format(name, reason))
		else:
			self.stdout.write(u"Deleting {0} {1} which {2}... ".format(count, name, reason))
			self.stdout.flush()
			queryset.delete()
			self.stdout.write("Done.\n")

	def _walk(self, dirpath, topdown=True):
		"""
		Recursively walks the dir with default_storage. Yields (dirpath, dirnames, filenames)
		tuples.

		"""
		try:
			dirnames, filenames = default_storage.listdir(dirpath)
		except NotImplementedError:
			# default_storage can't listdir.
			dirnames, filenames = [], []

		if topdown:
			yield dirpath, dirnames, filenames

		for dirname in dirnames:
			for value in self._walk(os.path.join(dirpath, dirname), topdown):
				yield value

		if not topdown:
			yield dirpath, dirnames, filenames

	def handle_noargs(self, **options):
		# First, clear all adjusted images that reference nonexistant
		# storage paths.
		storage_paths = AdjustedImage.objects.values_list('storage_path', flat=True).distinct()
		nonexistant = [path for path in storage_paths if not default_storage.exists(path)]
		self._delete_queryset(AdjustedImage.objects.filter(storage_path__in=nonexistant))

		# Second, clear all areas that reference nonexistant storage paths.
		storage_paths = Area.objects.values_list('storage_path', flat=True).distinct()
		nonexistant = [path for path in storage_paths if not default_storage.exists(path)]
		self._delete_queryset(Area.objects.filter(storage_path__in=nonexistant))

		# Now clear all duplicate adjusted images.
		fields = (
			'storage_path',
			'requested_width',
			'requested_height',
			'requested_crop',
			'requested_adjustment',
			'requested_max_width',
			'requested_max_height'
		)
		kwargs_list = AdjustedImage.objects.values(*fields
										  ).annotate(count=models.Count('id')
										  ).filter(count__gt=1
										  ).values(*fields)
		duplicate_pks = []
		for kwargs in kwargs_list:
			pks = AdjustedImage.objects.filter(**kwargs).values_list('pk', flat=True)
			duplicate_pks.extend(list(pks)[1:])
		self._delete_queryset(AdjustedImage.objects.filter(pk__in=duplicate_pks),
							  reason='is a duplicate',
							  reason_plural='are duplicates')

		# Now clean up files that aren't referenced by any adjusted images.
		known_paths = set(AdjustedImage.objects.values_list('adjusted', flat=True).distinct())
		orphaned_count = 0
		for dirpath, dirnames, filenames in self._walk('daguerre', topdown=False):
			for filename in filenames:
				filepath = os.path.join(dirpath, filename)
				if filepath not in known_paths:
					orphaned_count += 1
					try:
						default_storage.delete(filepath)
					except IOError:
						pass
		if not orphaned_count:
			self.stdout.write("No orphaned files found.\n")
		else:
			self.stdout.write("Deleted {0} orphaned file{1}.\n".format(orphaned_count, pluralize(orphaned_count)))

		self.stdout.write("\n")
