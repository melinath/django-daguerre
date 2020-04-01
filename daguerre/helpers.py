import datetime
import itertools
import ssl
import struct

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.http import QueryDict
from django.template import Variable, VariableDoesNotExist, TemplateSyntaxError
import six
from six.moves import http_client
try:
    from django.urls import reverse
except ImportError:
    # Compatibility for Django < 1.10
    from django.core.urlresolvers import reverse
try:
    from PIL import Image
except ImportError:
    import Image
try:
    import jingo
except ImportError:
    jingo = None

from daguerre.adjustments import registry, Adjustment
from daguerre.models import Area, AdjustedImage
from daguerre.utils import make_hash, save_image, get_image_dimensions, KEEP_FORMATS, DEFAULT_FORMAT

# If any of the following errors appear during file manipulations, we will
# treat them as IOErrors.
# See http://code.larlet.fr/django-storages/issue/162/reraise-boto-httplib-errors-as-ioerrors
IOERRORS = (IOError, http_client.IncompleteRead, ssl.SSLError)

try:
    import boto.exception
except ImportError:
    pass
else:
    IOERRORS = IOERRORS + (boto.exception.BotoServerError,
                           boto.exception.S3ResponseError)


def adjust(path_or_iterable, adjustment=None, lookup=None, generate=False, **kwargs):
    if isinstance(path_or_iterable, AdjustmentHelper):
        helper = path_or_iterable
    else:
        if isinstance(path_or_iterable, six.string_types):
            iterable = [path_or_iterable]
        elif isinstance(path_or_iterable, File):
            iterable = [path_or_iterable.name]
        else:
            try:
                iterable = list(path_or_iterable)
            except TypeError:
                iterable = [path_or_iterable]
        helper = AdjustmentHelper(iterable, lookup=lookup, generate=generate)
    if adjustment:
        helper.adjust(adjustment, **kwargs)
    return helper


if jingo:
    jingo.register.filter(adjust)


class AdjustmentInfoDict(dict):
    "A simple dict subclass for making image data more usable in templates."

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return six.text_type(self.get('url', ''))


class AdjustmentHelper(object):
    query_map = {
        'requested': 'r',
        'security': 's',
    }
    param_sep = '|'
    adjustment_sep = '>'

    def __init__(self, iterable, lookup=None, generate=False):
        # generate: whether iterating over this object should actually
        # run adjustments, or just return infodicts.
        self.adjustments = []
        self.iterable = list(iterable)
        self.lookup = lookup
        self.generate = generate
        self.remaining = {}
        self.adjusted = {}
        self.adjust_uses_areas = False
        self.calc_uses_areas = False
        self._finalized = False

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

    def __unicode__(self):
        try:
            return six.text_type(self[0][1])
        except IndexError:
            return u''

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return u"<{0}: {1}, {2}, {3}>".format(
            self.__class__.__name__,
            self.__class__._serialize_requested(self.adjustments),
            self.lookup,
            self.generate
        )

    def __iter__(self):
        if not self._finalized:
            self._finalize()
        for item in self.iterable:
            yield (item, self.adjusted[item])

    def __getitem__(self, key):
        if not self._finalized:
            self._finalize()
        if isinstance(key, slice):
            return [(item, self.adjusted[item])
                    for item in self.iterable]
        item = self.iterable[key]
        return item, self.adjusted[item]

    def adjust(self, key, **kwargs):
        if self._finalized:
            raise ValueError("Finalized helpers can't be adjusted.")
        if isinstance(key, Adjustment):
            if kwargs:
                raise ValueError("kwargs can't be specified with an "
                                 "adjustment instance")
            adj = key
        else:
            cls = registry[key]
            adj = cls(**kwargs)
        self.adjustments.append(adj)
        self.adjust_uses_areas = (self.adjust_uses_areas or
                                  getattr(adj.adjust, 'uses_areas', True))
        self.calc_uses_areas = (self.calc_uses_areas or
                                getattr(adj.calculate, 'uses_areas', True))
        return self

    @property
    def requested(self):
        return self._serialize_requested(self.adjustments)

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
            adj_cls = registry[bits[0]]
            kwargs = {}
            for i, bit in enumerate(bits[1:]):
                kwargs[adj_cls.parameters[i]] = bit or None
            adj_list.append(adj_cls(**kwargs))
        return adj_list

    def get_query_kwargs(self):
        kwargs = {
            'requested': self.requested
        }
        if len(self.remaining) == 1:
            kwargs['storage_path'] = list(self.remaining.keys())[0]
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
        keys_sorted = sorted(kwargs.keys())
        values = [kwargs[key] for key in keys_sorted]
        args = list(itertools.chain(keys_sorted, values))
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

        for k, v in six.iteritems(kwargs):
            qd[self.query_map[k]] = v

        return qd

    @classmethod
    def from_querydict(cls, image_or_storage_path, querydict, secure=False, generate=False):
        kwargs = {}
        for verbose, short in six.iteritems(cls.query_map):
            if short in querydict:
                kwargs[verbose] = querydict[short]

        if 'security' in kwargs:
            if not cls.check_security_hash(kwargs.pop('security'), kwargs):
                raise ValueError("Security check failed.")
        elif secure:
            raise ValueError("Security hash missing.")

        adjustments = cls._deserialize_requested(kwargs['requested'])
        helper = cls([image_or_storage_path], generate=generate)
        for adjustment in adjustments:
            helper.adjust(adjustment)
        return helper

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
            with default_storage.open(storage_path, 'rb') as im_file:
                width, height = get_image_dimensions(im_file)
        except IOERRORS + (TypeError,):
            # TypeError will be raised if for any reason storage_path's
            # dimensions can't be determined. get_image_dimensions will
            # return None, which can't be split into width and height.
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

    def _finalize(self):
        if not self.adjustments:
            raise ValueError("At least one adjustment must be provided.")
        if self._finalized:
            return

        self.finalized = True

        for item in self.iterable:
            path = self.lookup_func(item, None)
            if isinstance(path, File):
                path = path.name
            # Skip empty paths (such as from an ImageFieldFile with no image.)
            if path and isinstance(path, six.string_types):
                self.remaining.setdefault(path, []).append(item)
            else:
                self.adjusted[item] = AdjustmentInfoDict()

        if self.remaining:
            query_kwargs = self.get_query_kwargs()
            adjusted_images = AdjustedImage.objects.filter(**query_kwargs
                                                           ).defer('requested')
            for adjusted_image in adjusted_images:
                path = adjusted_image.storage_path
                if path not in self.remaining:
                    continue
                info_dict = self._adjusted_image_info_dict(adjusted_image)
                for item in self.remaining[path]:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

        if self.remaining:
            for path, items in six.iteritems(self.remaining.copy()):
                if self.generate is True:
                    try:
                        adjusted_image = self._generate(path)
                    except IOERRORS:
                        info_dict = AdjustmentInfoDict()
                    else:
                        info_dict = self._adjusted_image_info_dict(adjusted_image)
                else:
                    info_dict = self._path_info_dict(path)
                for item in items:
                    self.adjusted[item] = info_dict
                del self.remaining[path]

    def _generate(self, storage_path):
        # May raise IOError if the file doesn't exist or isn't a valid image.

        # If we're here, we can assume that the adjustment doesn't already
        # exist. Try to create one from the storage path. Raises IOError if
        # something goes wrong.
        kwargs = {
            'requested': self.requested,
            'storage_path': storage_path
        }

        with default_storage.open(storage_path, 'rb') as im_file:
            im = Image.open(im_file)
            try:
                im.verify()
            except (IndexError, struct.error, SyntaxError):
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

        args = (six.text_type(kwargs), datetime.datetime.now().isoformat())
        filename = '.'.join((make_hash(*args, step=2), format.lower()))
        storage_path = f.generate_filename(adjusted, filename)

        final_path = save_image(im, storage_path, format=format,
                                storage=default_storage)
        # Try to handle race conditions gracefully.
        try:
            adjusted = AdjustedImage.objects.filter(**kwargs
                                                    ).only('adjusted')[:1][0]
        except IndexError:
            adjusted.adjusted = final_path
            adjusted.save()
        else:
            default_storage.delete(final_path)
        return adjusted
