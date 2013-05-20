from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Model, get_model
from django.db.models.query import QuerySet
from django.template.defaultfilters import pluralize

from daguerre.adjustments import registry
from daguerre.models import AdjustedImage
from daguerre.helpers import AdjustmentHelper


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
        dp = settings.DAGUERRE_PREADJUSTMENTS
        args_list = []
        for (model_or_queryset, lookup), kwargs_list in dp.iteritems():
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
                adj_cls = registry[kwargs.pop('adjustment')]
                args_list.append((queryset, [adj_cls(**kwargs)], lookup))

        empty_count = 0
        skipped_count = 0
        helpers = []
        remaining_count = 0
        for args in args_list:
            helper = AdjustmentHelper(*args)
            helper.empty_count = len(helper.adjusted)
            empty_count += helper.empty_count
            helper._fetch_adjusted()
            skipped_count += len(helper.adjusted) - helper.empty_count
            remaining_count += len(helper.remaining)
            helpers.append(helper)

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

        if options['remove']:
            queryset = AdjustedImage.objects.all()
            for args in args_list:
                helper = AdjustmentHelper(*args)
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

        # For pre-1.5: add an extra newline.
        self.stdout.write("\n")
