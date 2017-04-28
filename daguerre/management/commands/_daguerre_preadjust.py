from __future__ import absolute_import

from optparse import make_option

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from django.db.models.query import QuerySet
from django.template.defaultfilters import pluralize
import six

from daguerre.models import AdjustedImage
from daguerre.helpers import AdjustmentHelper, IOERRORS


NO_ADJUSTMENTS = """No adjustments were defined.
You'll need to add a DAGUERRE_PREADJUSTMENTS setting.
See the django-daguerre documentation for more details.
"""

BAD_STRUCTURE = """DAGUERRE_PREADJUSTMENTS should be an iterable of
tuples, where each tuple contains three items:

1. "<applabel>.<model>", a model class, a queryset, or any iterable.
2. A non-empty iterable of adjustment instances to be applied to each image.
3. A template-style lookup (or None).

See the django-daguerre documentation for more details.

"""


# Store option kwargs as consts so that we can reuse them
# between compatibility sets
REMOVE_OPTION_KWARGS = {
    'action': 'store_true',
    'dest': 'remove',
    'default': False,
    'help': "Remove all adjustments that aren't listed in DAGUERRE_PREADJUSTMENTS",
}

NOCREATE_OPTION_KWARGS = {
    'action': 'store_true',
    'dest': 'nocreate',
    'default': False,
    'help': "Don't create any new adjustments."
}


class Command(BaseCommand):
    if hasattr(BaseCommand, 'option_list'):
        # Django < 1.10
        option_list = BaseCommand.option_list + (
            make_option('--remove', **REMOVE_OPTION_KWARGS),
            make_option('--nocreate', **NOCREATE_OPTION_KWARGS),
        )
    else:
        # Django >= 1.10
        def add_arguments(self, parser):
            parser.add_argument('--remove', **REMOVE_OPTION_KWARGS)
            parser.add_argument('--nocreate', **NOCREATE_OPTION_KWARGS)

    def _get_helpers(self):
        if not hasattr(settings, 'DAGUERRE_PREADJUSTMENTS'):
            raise CommandError(NO_ADJUSTMENTS)
        dp = settings.DAGUERRE_PREADJUSTMENTS
        if not hasattr(self, '_helpers'):
            self._helpers = []
            try:
                for (model_or_iterable, adjustments, lookup) in dp:
                    if isinstance(model_or_iterable, six.string_types):
                        app_label, model_name = model_or_iterable.split('.')
                        model_or_iterable = apps.get_model(app_label, model_name)
                    if (isinstance(model_or_iterable, six.class_types) and
                            issubclass(model_or_iterable, Model)):
                        iterable = model_or_iterable.objects.all()
                    elif isinstance(model_or_iterable, QuerySet):
                        iterable = model_or_iterable._clone()
                    else:
                        iterable = model_or_iterable

                    helper = AdjustmentHelper(iterable, lookup=lookup, generate=False)
                    for adjustment in adjustments:
                        helper.adjust(adjustment)
                    helper._finalize()
                    self._helpers.append(helper)
            except (ValueError, TypeError, LookupError):
                raise CommandError(BAD_STRUCTURE)

        return self._helpers

    def _preadjust(self):
        empty_count = 0
        skipped_count = 0
        remaining_count = 0
        helpers = self._get_helpers()
        for helper in helpers:
            empty_count += len([info_dict for info_dict in six.itervalues(helper.adjusted)
                                if not info_dict])
            skipped_count += len([info_dict for info_dict in six.itervalues(helper.adjusted)
                                  if info_dict and 'ajax_url' not in info_dict])
            remaining_count += len(helper.adjusted) - skipped_count - empty_count

        self.stdout.write(
            "Skipped {0} empty path{1}.\n".format(
                empty_count,
                pluralize(empty_count)))

        self.stdout.write(
            "Skipped {0} path{1} which ha{2} already been adjusted.\n".format(
                skipped_count,
                pluralize(skipped_count),
                pluralize(skipped_count, 's,ve')))

        if remaining_count == 0:
            self.stdout.write("No paths remaining to adjust.\n")
        else:
            self.stdout.write("Adjusting {0} path{1}... ".format(
                remaining_count,
                pluralize(remaining_count)))
            self.stdout.flush()

            failed_count = 0
            for helper in helpers:
                remaining = {}
                for item, info_dict in six.iteritems(helper.adjusted):
                    # Skip if missing
                    if not info_dict:
                        continue
                    # Skip if already adjusted
                    if 'ajax_url' not in info_dict:
                        continue

                    remaining.setdefault(helper.lookup_func(item, None), []).append(item)

                for path, items in six.iteritems(remaining):
                    try:
                        helper._generate(path)
                    except IOERRORS:
                        failed_count += 1
            self.stdout.write("Done.\n")
            if failed_count:
                self.stdout.write(
                    "{0} path{1} failed due to I/O errors.".format(
                        failed_count,
                        pluralize(failed_count)))

    def _prune(self):
        queryset = AdjustedImage.objects.all()
        helpers = self._get_helpers()
        for helper in helpers:
            query_kwargs = helper.get_query_kwargs()
            queryset = queryset.exclude(**query_kwargs)

        count = queryset.count()
        if count == 0:
            self.stdout.write("No adjusted images found to remove.\n")
        else:
            self.stdout.write("Removing {0} adjusted image{1}... ".format(
                count,
                pluralize(count)))
            self.stdout.flush()
            queryset.delete()
            self.stdout.write("Done.\n")

    def handle(self, **options):
        if options['nocreate'] and not options['remove']:
            self.stdout.write("Doing nothing.\n")

        if not options['nocreate']:
            self._preadjust()

        if options['remove']:
            self._prune()

        # For pre-1.5: add an extra newline.
        self.stdout.write("\n")
