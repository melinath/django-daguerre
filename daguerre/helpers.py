import datetime

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.template import Variable, VariableDoesNotExist, TemplateSyntaxError
from django.utils.datastructures import SortedDict
try:
    from PIL import Image
except ImportError:
    import Image

from daguerre.adjustments import (DEFAULT_ADJUSTMENT, get_adjustment_class,
                                  deserialize)
from daguerre.models import Area, AdjustedImage
from daguerre.utils import make_hash, save_image, KEEP_FORMATS, DEFAULT_FORMAT


ADJUSTMENT_SEP = '>'


class AdjustmentInfoDict(dict):
    "A simple dict subclass for making image data more usable in templates."

    def __unicode__(self):
        return self.get('url', u'')


class BaseAdjustmentHelper(object):
    param_map = {
        'requested': 'r',
        'security': 's',
    }

    def __init__(self, *adjustments):
        self.adjustments = adjustments
        self.adjust_uses_areas = any([getattr(adj.adjust, 'uses_areas', True)
                                      for adj in adjustments])
        self.calc_uses_areas = any([getattr(adj.calculate, 'uses_areas', True)
                                    for adj in adjustments])
        adj_strings = [adj.serialize() for adj in adjustments]
        self.requested = ADJUSTMENT_SEP.join(adj_strings)

    def get_query_kwargs(self):
        return {
            'requested': self.requested
        }

    def _open_image(self, storage_path):
        # Will raise IOError if the file doesn't exist or isn't a valid image.
        im_file = default_storage.open(storage_path)
        im = Image.open(im_file)
        try:
            im.verify()
        except Exception:
            # Raise an IOError if the image isn't valid.
            raise IOError
        im_file.seek(0)
        return Image.open(im_file)

    def _adjusted_image_info_dict(self, adjusted_image):
        im = Image.open(adjusted_image.adjusted)
        return AdjustmentInfoDict({
            'width': im.size[0],
            'height': im.size[1],
            'url': adjusted_image.adjusted.url,
        })

    @classmethod
    def make_security_hash(cls, kwargs):
        kwargs = SortedDict(kwargs)
        kwargs.keyOrder.sort()
        args = kwargs.keys() + kwargs.values()
        return make_hash(settings.SECRET_KEY, step=2, *args)

    def to_querydict(self, secure=False):
        qd = QueryDict('', mutable=True)
        kwargs = {
            'requested': self.requested
        }

        if secure:
            kwargs['security'] = self.make_security_hash(kwargs)

        for k, v in kwargs.iteritems():
            qd[self.param_map[k]] = v

        return qd

    def _path_info_dict(self, storage_path):
        try:
            im = self._open_image(storage_path)
        except IOError:
            return AdjustmentInfoDict()

        if self.calc_uses_areas:
            areas = self.get_areas(storage_path)
        else:
            areas = None

        width, height = im.size
        for adjustment in self.adjustments:
            width, height = adjustment.calculate((width, height), areas=areas)

        url = u"{0}?{1}".format(
            reverse('daguerre_adjusted_image_redirect',
                    kwargs={'storage_path': storage_path}),
            self.to_querydict(secure=True).urlencode()
        )
        ajax_url = u"{0}?{1}".format(
            reverse('daguerre_ajax_adjustment_info',
                    kwargs={'storage_path': storage_path}),
            self.to_querydict(secure=False).urlencode()
        )
        return AdjustmentInfoDict({
            'width': width,
            'height': height,
            'url': url,
            'ajax_url': ajax_url,
        })


class AdjustmentHelper(BaseAdjustmentHelper):
    int_params = set(('width', 'height', 'max_width', 'max_height'))

    def __init__(self, image_or_storage_path, *adjustments):
        if isinstance(image_or_storage_path, ImageFile):
            self.storage_path = image_or_storage_path.name
        else:
            self.storage_path = image_or_storage_path

        super(AdjustmentHelper, self).__init__(*adjustments)

    def get_areas(self, storage_path):
        if not hasattr(self, '_areas'):
            self._areas = Area.objects.filter(storage_path=storage_path)
        return self._areas

    def get_query_kwargs(self):
        query_kwargs = super(AdjustmentHelper, self).get_query_kwargs()
        query_kwargs['storage_path'] = self.storage_path
        return query_kwargs

    @classmethod
    def check_security_hash(cls, sec_hash, kwargs):
        return sec_hash == cls.make_security_hash(kwargs)

    @classmethod
    def from_querydict(cls, image_or_storage_path, querydict, secure=False):
        kwargs = SortedDict()
        for verbose, short in cls.param_map.iteritems():
            if short in querydict:
                kwargs[verbose] = querydict[short]

        if 'security' in kwargs:
            if not cls.check_security_hash(kwargs.pop('security'), kwargs):
                raise ValueError("Security check failed.")
        elif secure:
            raise ValueError("Security hash missing.")

        adj_strings = kwargs['requested'].split(ADJUSTMENT_SEP)
        adjustments = [deserialize(string) for string in adj_strings]

        return cls(image_or_storage_path, *adjustments)

    def info_dict(self):
        """
        Main method. The AdjustmentHelper should be able to calculate
        an appropriate info dict with minimal effort just by running
        this method.

        """
        kwargs = self.get_query_kwargs()

        # If there's no storage path, don't even bother trying.
        if self.storage_path:
            # First try to fetch a previously-adjusted image and return
            # its info dict.
            try:
                adjusted = AdjustedImage.objects.filter(**kwargs)[:1][0]
            except IndexError:
                pass
            else:
                return self._adjusted_image_info_dict(adjusted)

            # If that fails, do a lazy adjustment based on the path.
            return self._path_info_dict(self.storage_path)
        return AdjustmentInfoDict()

    def adjust(self):
        # May raise IOError.

        # First try to fetch a version that already exists.
        kwargs = self.get_query_kwargs()
        try:
            return AdjustedImage.objects.filter(**kwargs)[:1][0]
        except IndexError:
            pass

        # If that fails, try to create one from the storage path.
        # Raises IOError if something goes wrong.

        im = self._open_image(self.storage_path)
        format = im.format if im.format in KEEP_FORMATS else DEFAULT_FORMAT

        if self.adjust_uses_areas:
            areas = self.get_areas(self.storage_path)
        else:
            areas = None

        for adjustment in self.adjustments:
            im = adjustment.adjust(im, areas=areas)

        adjusted = AdjustedImage(**kwargs)
        f = adjusted._meta.get_field('adjusted')

        args = (unicode(kwargs), datetime.datetime.now().isoformat())
        filename = '.'.join((make_hash(*args, step=2), format.lower()))
        storage_path = f.generate_filename(adjusted, filename)

        final_path = save_image(im, storage_path, format=format,
                                storage=default_storage)
        # Try to handle race conditions gracefully.
        try:
            adjusted = AdjustedImage.objects.filter(**kwargs)[:1][0]
        except IndexError:
            adjusted.adjusted = final_path
            adjusted.save()
        else:
            default_storage.delete(final_path)
        return adjusted


class BulkAdjustmentHelper(BaseAdjustmentHelper):
    def __init__(self, iterable, lookup, *adjustments):
        self.iterable = list(iterable)
        self.lookup = lookup
        self.remaining = {}
        self.adjusted = {}

        try:
            lookup_var = Variable("item.{0}".format(lookup))
        except TemplateSyntaxError:
            lookup_func = lambda *args, **kwargs: None
        else:
            def lookup_func(obj, default=None):
                try:
                    return lookup_var.resolve({'item': obj})
                except VariableDoesNotExist:
                    return default

        self.lookup_func = lookup_func

        for item in iterable:
            path = self.lookup_func(item, None)
            if isinstance(path, ImageFile):
                path = path.name
            # Skip empty paths (such as from an ImageFieldFile with no image.)
            if path and isinstance(path, basestring):
                self.remaining.setdefault(path, []).append(item)
            else:
                self.adjusted[item] = AdjustmentInfoDict()

        super(BulkAdjustmentHelper, self).__init__(*adjustments)

    def get_areas(self, storage_path):
        if not hasattr(self, '_areas'):
            self._areas = {}
            areas = Area.objects.filter(storage_path__in=self.remaining)
            for area in areas:
                self._areas.setdefault(area.storage_path, []).append(area)
        return self._areas.get(storage_path, [])

    def get_query_kwargs(self):
        query_kwargs = super(BulkAdjustmentHelper, self).get_query_kwargs()
        query_kwargs['storage_path__in'] = self.remaining
        return query_kwargs

    def info_dicts(self):
        # First, try to fetch all previously-adjusted images.
        if self.remaining:
            query_kwargs = self.get_query_kwargs()
            adjusted_images = AdjustedImage.objects.filter(**query_kwargs)
            for adjusted_image in adjusted_images:
                path = adjusted_image.storage_path
                if path not in self.remaining:
                    continue
                info_dict = self._adjusted_image_info_dict(adjusted_image)
                for item in self.remaining[path]:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

        # And then make adjustment dicts for any remaining paths.
        if self.remaining:
            for path, items in self.remaining.copy().iteritems():
                info_dict = self._path_info_dict(path)
                for item in items:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

        return [(item, self.adjusted[item]) for item in self.iterable]
