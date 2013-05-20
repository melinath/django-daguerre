import datetime
import httplib
import ssl

from django.conf import settings
from django.core.files.images import ImageFile, get_image_dimensions
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.template import Variable, VariableDoesNotExist, TemplateSyntaxError
from django.utils.datastructures import SortedDict
try:
    from PIL import Image
except ImportError:
    import Image

from daguerre.adjustments import adjustments
from daguerre.models import Area, AdjustedImage
from daguerre.utils import make_hash, save_image, KEEP_FORMATS, DEFAULT_FORMAT


# If any of the following errors appear during file manipulations, we will
# treat them as IOErrors.
# See http://code.larlet.fr/django-storages/issue/162/reraise-boto-httplib-errors-as-ioerrors
IOERRORS = (IOError, httplib.IncompleteRead, ssl.SSLError)

try:
    import boto.exception
except ImportError:
    pass
else:
    IOERRORS = IOERRORS + (boto.exception.BotoServerError,
                           boto.exception.S3ResponseError)


class AdjustmentInfoDict(dict):
    "A simple dict subclass for making image data more usable in templates."

    def __unicode__(self):
        return unicode(self.get('url', ''))


class AdjustmentHelper(object):
    query_map = {
        'requested': 'r',
        'security': 's',
    }
    param_sep = '|'
    adjustment_sep = '>'

    def __init__(self, iterable, adjustments, lookup=None):
        self.adjustments = adjustments
        self.adjust_uses_areas = any([getattr(adj.adjust, 'uses_areas', True)
                                      for adj in adjustments])
        self.calc_uses_areas = any([getattr(adj.calculate, 'uses_areas', True)
                                    for adj in adjustments])
        self.requested = self._serialize_requested(adjustments)

        self.iterable = list(iterable)
        self.lookup = lookup
        self.remaining = {}
        self.adjusted = {}

        if lookup is None:
            lookup_func = lambda obj, default=None: obj
        else:
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

    @classmethod
    def _serialize_requested(cls, adjustments):
        adj_strings = []
        for adj in adjustments:
            bits = [adj.__class__.__name__.lower()]
            bits += [str(adj.kwargs.get(key) or '')
                     for key in adj.parameters]
            adj_strings.append(cls.param_sep.join(bits))
        return cls.adjustment_sep.join(adj_strings)

    @classmethod
    def _deserialize_requested(cls, requested):
        adj_list = []
        for adj_string in requested.split(cls.adjustment_sep):
            bits = adj_string.split(cls.param_sep)
            cls = adjustments[bits[0]]
            kwargs = {}
            for i, bit in enumerate(bits[1:]):
                kwargs[cls.parameters[i]] = bit or None
            adj_list.append(cls(**kwargs))
        return adj_list

    def get_query_kwargs(self):
        kwargs = {
            'requested': self.requested
        }
        if len(self.remaining) == 1:
            kwargs['storage_path'] = self.remaining.keys()[0]
        else:
            kwargs['storage_path__in'] = self.remaining
        return kwargs

    def get_areas(self, storage_path):
        if not hasattr(self, '_areas'):
            self._areas = {}
            areas = Area.objects.filter(storage_path__in=self.remaining)
            for area in areas:
                self._areas.setdefault(area.storage_path, []).append(area)
        return self._areas.get(storage_path, [])

    @classmethod
    def make_security_hash(cls, kwargs):
        kwargs = SortedDict(kwargs)
        kwargs.keyOrder.sort()
        args = kwargs.keys() + kwargs.values()
        return make_hash(settings.SECRET_KEY, step=2, *args)

    @classmethod
    def check_security_hash(cls, sec_hash, kwargs):
        return sec_hash == cls.make_security_hash(kwargs)

    def to_querydict(self, secure=False):
        qd = QueryDict('', mutable=True)
        kwargs = {
            'requested': self.requested
        }

        if secure:
            kwargs['security'] = self.make_security_hash(kwargs)

        for k, v in kwargs.iteritems():
            qd[self.query_map[k]] = v

        return qd

    @classmethod
    def from_querydict(cls, image_or_storage_path, querydict, secure=False):
        kwargs = SortedDict()
        for verbose, short in cls.query_map.iteritems():
            if short in querydict:
                kwargs[verbose] = querydict[short]

        if 'security' in kwargs:
            if not cls.check_security_hash(kwargs.pop('security'), kwargs):
                raise ValueError("Security check failed.")
        elif secure:
            raise ValueError("Security hash missing.")

        adjustments = cls._deserialize_requested(kwargs['requested'])
        return cls([image_or_storage_path], adjustments)

    def _adjusted_image_info_dict(self, adjusted_image):
        try:
            width, height = adjusted_image.adjusted._get_image_dimensions()
        except IOERRORS:
            return AdjustmentInfoDict()

        return AdjustmentInfoDict({
            'width': width,
            'height': height,
            'url': adjusted_image.adjusted.url,
        })

    def _path_info_dict(self, storage_path):
        try:
            with default_storage.open(storage_path) as im_file:
                width, height = get_image_dimensions(im_file)
        except IOERRORS:
            return AdjustmentInfoDict()

        if self.calc_uses_areas:
            areas = self.get_areas(storage_path)
        else:
            areas = None

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

    def _fetch_adjusted(self):
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

    def info_dicts(self):
        self._fetch_adjusted()

        # And then make adjustment dicts for any remaining paths.
        if self.remaining:
            for path, items in self.remaining.copy().iteritems():
                info_dict = self._path_info_dict(path)
                for item in items:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

        return [(item, self.adjusted[item]) for item in self.iterable]

    def adjust(self):
        self._fetch_adjusted()

        if self.remaining:
            for path, items in self.remaining.copy().iteritems():
                try:
                    adjusted_image = self._adjust(path)
                except IOERRORS:
                    info_dict = AdjustmentInfoDict()
                else:
                    info_dict = self._adjusted_image_info_dict(adjusted_image)
                for item in items:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

    def _adjust(self, storage_path):
        # May raise IOError if the file doesn't exist or isn't a valid image.

        # If we're here, we can assume that the adjustment doesn't already
        # exist. Try to create one from the storage path. Raises IOError if
        # something goes wrong.
        kwargs = {
            'requested': self.requested,
            'storage_path': storage_path
        }

        with default_storage.open(storage_path) as im_file:
            im = Image.open(im_file)
            try:
                im.verify()
            except Exception:
                # Raise an IOError if the image isn't valid.
                raise IOError
            im_file.seek(0)
            im = Image.open(im_file)
            im.load()
        format = im.format if im.format in KEEP_FORMATS else DEFAULT_FORMAT

        if self.adjust_uses_areas:
            areas = self.get_areas(storage_path)
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
