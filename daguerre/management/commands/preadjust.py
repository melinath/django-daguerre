from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Model, get_model
from django.db.models.query import QuerySet
from django.template.defaultfilters import pluralize

from daguerre.models import AdjustedImage
from daguerre.helpers import AdjustmentHelper, BulkAdjustmentHelper


NO_ADJUSTMENTS = """No adjustments were defined.
You'll need to add a DAGUERRE_PREADJUSTMENTS
setting. See the documentation for more details.
"""


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--remove',
            action='store_true',
            dest='remove',
            default=False,
            help=(
                "Remove all adjustments that aren't"
                " listed in DAGUERRE_ADJUSTMENTS"),
        ),
    )

    def handle_noargs(self, **options):
        if not hasattr(settings, 'DAGUERRE_PREADJUSTMENTS'):
            raise CommandError(NO_ADJUSTMENTS)
        adjustments = settings.DAGUERRE_PREADJUSTMENTS
        args = []
        for (model_or_queryset, lookup), kwargs_list in adjustments.iteritems():
            if isinstance(model_or_queryset, basestring):
                app_label, model_name = model_or_queryset.split('.')
                model_or_queryset = get_model(app_label, model_name)
            if issubclass(model_or_queryset, Model):
                queryset = model_or_queryset.objects.all()
            elif isinstance(model_or_queryset, QuerySet):
                queryset = model_or_queryset._clone()
            else:
                raise CommandError(
                    "Invalid model or queryset: {0}".format(
                        model_or_queryset))

            for kwargs in kwargs_list:
                args.append((queryset, lookup, kwargs))

        skipped_count = 0
        remaining = []
        remaining_count = 0
        for queryset, lookup, kwargs in args:
            bulk_helper = BulkAdjustmentHelper(queryset, lookup, **kwargs)
            query_kwargs = bulk_helper.get_query_kwargs()
            adjusted_images = AdjustedImage.objects.filter(**query_kwargs)
            for adjusted_image in adjusted_images:
                try:
                    del bulk_helper.remaining[adjusted_image.storage_path]
                except KeyError:
                    pass
                else:
                    skipped_count += 1
            remaining_count += len(bulk_helper.remaining)
            remaining.append((bulk_helper.remaining.keys(), kwargs))

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
            for storage_paths, kwargs in remaining:
                for storage_path in storage_paths:
                    helper = AdjustmentHelper(storage_path, **kwargs)
                    try:
                        helper.adjust()
                    except IOError:
                        failed_count += 1
            self.stdout.write("Done.\n")
            if failed_count:
                self.stdout.write(
                    "{0} path{1} failed due to I/O errors.".format(
                        failed_count,
                        pluralize(failed_count)))

        if options['remove']:
            queryset = AdjustedImage.objects.all()
            for qs, lookup, kwargs in args:
                bulk_helper = BulkAdjustmentHelper(qs, lookup, **kwargs)
                query_kwargs = bulk_helper.get_query_kwargs()
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

        # For pre-1.5: add an extra newline.
        self.stdout.write("\n")
