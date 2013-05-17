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

from daguerre.adjustments import DEFAULT_ADJUSTMENT, get_adjustment_class
from daguerre.models import Area, AdjustedImage
from daguerre.utils import make_hash, save_image, KEEP_FORMATS, DEFAULT_FORMAT


class AdjustmentInfoDict(dict):
    "A simple dict subclass for making image data more usable in templates."

    def __unicode__(self):
        return self.get('url', u'')


class BaseAdjustmentHelper(object):
    param_map = {
        'width': 'w',
        'height': 'h',
        'max_width': 'max_w',
        'max_height': 'max_h',
        'adjustment': 'a',
        'security': 's',
        'crop': 'c'
    }

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.adjustment = kwargs.pop('adjustment', DEFAULT_ADJUSTMENT)
        self.adjustment_class = get_adjustment_class(self.adjustment)

    def get_crop_area(self):
        return None

    def get_query_kwargs(self):
        if not hasattr(self, '_query_kwargs'):
            query_kwargs = {
                'requested_adjustment': self.adjustment,
            }
            for key in ('width', 'height', 'max_width', 'max_height'):
                value = self.kwargs.get(key)
                if value is None:
                    query_kwargs['requested_{0}__isnull'.format(key)] = True
                else:
                    query_kwargs['requested_{0}'.format(key)] = value
            area = self.get_crop_area()
            if area is None:
                query_kwargs['requested_crop__isnull'] = True
            else:
                query_kwargs['requested_crop'] = area
            self._query_kwargs = query_kwargs
        return self._query_kwargs

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

    def adjustment_for_image(self, image):
        return self.adjustment_class(image, **self.kwargs)

    def _adjusted_image_info_dict(self, adjusted_image):
        return AdjustmentInfoDict({
            'width': adjusted_image.width,
            'height': adjusted_image.height,
            'requested': {
                'width': adjusted_image.requested_width,
                'height': adjusted_image.requested_height,
                'max_width': adjusted_image.requested_max_width,
                'max_height': adjusted_image.requested_max_height,
            },
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
        kwargs = self.kwargs.copy()
        kwargs['adjustment'] = self.adjustment

        if secure:
            kwargs['security'] = self.make_security_hash(kwargs)

        for k, v in kwargs.iteritems():
            qd[self.param_map[k]] = v

        return qd

    def _path_info_dict(self, storage_path):
        try:
            im = self._open_image(storage_path)
            adjustment = self.adjustment_for_image(im)
        except IOError:
            return AdjustmentInfoDict()
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
            'width': adjustment.calculate()[0],
            'height': adjustment.calculate()[1],
            'requested': self.kwargs.copy(),
            'url': url,
            'ajax_url': ajax_url,
        })


class AdjustmentHelper(BaseAdjustmentHelper):
    int_params = set(('width', 'height', 'max_width', 'max_height'))

    def __init__(self, image_or_storage_path, **kwargs):
        if isinstance(image_or_storage_path, ImageFile):
            self.storage_path = image_or_storage_path.name
        else:
            self.storage_path = image_or_storage_path

        super(AdjustmentHelper, self).__init__(**kwargs)

    def get_areas(self):
        if not hasattr(self, '_areas'):
            self._areas = Area.objects.filter(storage_path=self.storage_path)
        return self._areas

    def get_crop_area(self):
        if not hasattr(self, '_crop_area'):
            area = None
            if 'crop' in self.kwargs:
                try:
                    area = self.get_areas().get(name=self.kwargs['crop'])
                except Area.DoesNotExist:
                    pass
            self._crop_area = area
        return self._crop_area

    def get_query_kwargs(self):
        if not hasattr(self, '_query_kwargs'):
            super(AdjustmentHelper, self).get_query_kwargs()
            self._query_kwargs['storage_path'] = self.storage_path
        return self._query_kwargs

    @classmethod
    def check_security_hash(cls, sec_hash, kwargs):
        return sec_hash == cls.make_security_hash(kwargs)

    @classmethod
    def from_querydict(cls, image_or_storage_path, querydict, secure=False):
        kwargs = SortedDict()
        for verbose, short in cls.param_map.iteritems():
            try:
                value = querydict[short]
            except KeyError:
                continue
            if verbose in cls.int_params:
                # Raises ValueError if it can't be converted.
                value = int(value)
            kwargs[verbose] = value

        if 'security' in kwargs:
            if not cls.check_security_hash(kwargs.pop('security'), kwargs):
                raise ValueError("Security check failed.")
        elif secure:
            raise ValueError("Security hash missing.")

        return cls(image_or_storage_path, **kwargs)

    def adjustment_for_image(self, image):
        crop_area = self.get_crop_area()
        if crop_area is None:
            areas = self.get_areas()
        else:
            # Ignore areas if there is a valid crop, for now.
            # Maybe someday "crop" the areas and pass them in.
            areas = None
            image = image.crop((crop_area.x1, crop_area.y1,
                                crop_area.x2, crop_area.y2))

        kwargs = self.kwargs.copy()
        kwargs.pop('crop', None)

        return self.adjustment_class(image, areas=areas, **kwargs)

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
        adjustment = self.adjustment_for_image(im)
        im = adjustment.adjust()

        creation_kwargs = {}
        for k, v in kwargs.iteritems():
            if k.endswith('__isnull'):
                creation_kwargs[k[:-len('__isnull')]] = None
            else:
                creation_kwargs[k] = v

        adjusted = AdjustedImage(**creation_kwargs)
        f = adjusted._meta.get_field('adjusted')

        args = (unicode(creation_kwargs), datetime.datetime.now().isoformat())
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
    def __init__(self, iterable, lookup, **kwargs):
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

        super(BulkAdjustmentHelper, self).__init__(**kwargs)

    def get_query_kwargs(self):
        if not hasattr(self, '_query_kwargs'):
            super(BulkAdjustmentHelper, self).get_query_kwargs()
            self._query_kwargs['storage_path__in'] = self.remaining
        return self._query_kwargs

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
