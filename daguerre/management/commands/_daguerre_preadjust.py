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
from daguerre.helpers import AdjustmentHelper


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


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--remove',
            action='store_true',
            dest='remove',
            default=False,
            help="Remove all adjustments that aren't "
                 "listed in DAGUERRE_PREADJUSTMENTS",
        ),
        make_option(
            '--nocreate',
            action='store_true',
            dest='nocreate',
            default=False,
            help="Don't create any new adjustments."
        ),
    )

    def _get_helpers(self):
        if not hasattr(settings, 'DAGUERRE_PREADJUSTMENTS'):
            raise CommandError(NO_ADJUSTMENTS)
        dp = settings.DAGUERRE_PREADJUSTMENTS
        helpers = []
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

                helper = AdjustmentHelper(iterable, lookup=lookup, generate=True)
                for adjustment in adjustments:
                    helper.adjust(adjustment)
                helper._finalize()
                helpers.append(helper)
        except (ValueError, TypeError, LookupError):
            raise CommandError(BAD_STRUCTURE)

        return helpers

    def _preadjust(self):
        empty_count = 0
        skipped_count = 0
        remaining_count = 0
        helpers = self._get_helpers()
        for helper in helpers:
            helper.empty_count = len(helper.adjusted)
            empty_count += helper.empty_count
            helper._fetch_adjusted()
            skipped_count += len(helper.adjusted) - helper.empty_count
            remaining_count += len(helper.remaining)

        self.stdout.write(
            "Skipped {0} empty path{1}.\n".format(
                empty_count,
                pluralize(skipped_count)))

        self.stdout.write(
            "Skipped {0} path{1} which have already been adjusted.\n".format(
                skipped_count,
                pluralize(skipped_count)))

        if remaining_count == 0:
            self.stdout.write("No paths remaining to adjust.\n")
        else:
            self.stdout.write("Adjusting {0} path{1}... ".format(
                remaining_count,
                pluralize(remaining_count)))
            self.stdout.flush()

            failed_count = 0
            for helper in helpers:
                helper.adjust()
                empty_count = len([info_dict
                                   for info_dict in helper.adjusted.values()
                                   if not info_dict])
                failed_count += empty_count - helper.empty_count
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
