import datetime
from itertools import ifilter

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

from daguerre.models import Area, AdjustedImage
from daguerre.utils import make_hash, save_image, KEEP_FORMATS, DEFAULT_FORMAT


adjustments = {}
DEFAULT_ADJUSTMENT = 'fill'


def get_adjustment_class(slug):
    """Instantiates and returns the adjustment registered as ``slug``,
    or the default adjustment if no matching adjustment is found.
    The remaining arguments are passed directly to the adjustment class
    to create the instance."""
    try:
        return adjustments[slug]
    except KeyError:
        return adjustments[DEFAULT_ADJUSTMENT]


class Adjustment(object):
    """
    Base class for all adjustments which can be carried out on an image. Each
    adjustment has two stages: calculating the new image dimensions, and
    carrying out the adjustment.

    :param image: A PIL Image instance which is to be adjusted.
    :param width, height, max_width, max_height: The requested dimensions for
    the adjusted image.
    :param areas: :class:`~Area` instances representing protected areas for the
    adjustment.

    """

    #: Keeps track of whether or not this adjustment uses areas, so that we
    #: know whether to delete the cached adjusted images when a new area is
    #: defined or deleted.
    uses_areas = False

    def __init__(self, image, width=None, height=None, max_width=None,
                 max_height=None, areas=None):
        self.image = image
        self.format = self.image.format

        self.areas = areas

        self.width = width
        self.height = height
        self.max_width = max_width
        self.max_height = max_height

    def calculate(self):
        """
        Calculates the dimensions of the adjusted image without actually
        manipulating the image.

        """
        if not hasattr(self, '_calculated'):
            calculated = self._calculate()
            if calculated[0] <= 0 or calculated[1] <= 0:
                calculated = self.image.size
            self._calculated = calculated
        return self._calculated

    def _calculate(self):
        raise NotImplementedError

    def adjust(self):
        """Manipulates and returns the image."""
        if not hasattr(self, '_adjusted'):
            calculated = self.calculate()
            if calculated == self.image.size:
                adjusted = self.image.copy()
            else:
                adjusted = self._adjust()
            self._adjusted = adjusted
        return self._adjust()

    def _adjust(self):
        raise NotImplementedError


class Fit(Adjustment):
    """
    Resizes an image to fit entirely within the given dimensions
    without cropping and maintaining the width/height ratio.

    Rather than constraining an image to a specific width and height,
    ``width`` or ``height`` may be given as ``None``, in which case
    the image can expand in the unspecified direction up to
    ``max_width`` or ``max_height``, respectively, or indefinitely
    if the relevant dimension is not specified.

    If neither width nor height is specified, this adjustment will simply
    return a copy of the image.
    """
    def _calculate(self):
        image_width, image_height = self.image.size

        if self.width is None and self.height is None:
            return image_width, image_height

        image_ratio = float(image_width) / image_height

        if self.height is None:
            # Constrain first by width, then by max_height.
            new_height = int(self.width / image_ratio)
            new_width = int(self.width)
            if self.max_height is not None and new_height > self.max_height:
                new_height = int(self.max_height)
                new_width = int(new_height * image_ratio)
        elif self.width is None:
            # Constrain first by height, then by max_width.
            new_width = int(self.height * image_ratio)
            new_height = int(self.height)
            if self.max_width is not None and new_width > self.max_width:
                new_width = int(self.max_width)
                new_height = int(new_width / image_ratio)
        else:
            # Constrain strictly by both dimensions.
            new_width = int(min(self.width, self.height * image_ratio))
            new_height = int(min(self.height, self.width / image_ratio))

        return new_width, new_height

    def _adjust(self):
        image_width, image_height = self.image.size
        new_width, new_height = self.calculate()

        # Choose a resize filter based on whether
        # we're upscaling or downscaling.
        if new_width < image_width:
            f = Image.ANTIALIAS
        else:
            f = Image.BICUBIC
        return self.image.resize((new_width, new_height), f)


class Crop(Adjustment):
    """
    Crops an image to the given width and height, without scaling it.
    :class:`~daguerre.models.Area` instances which are passed in will be
    protected as much as possible during the crop. If ``width`` or
    ``height`` is not specified, the image may grow up to ``max_width``
    or ``max_height`` respectively in the unspecified direction before being
    cropped.

    """
    uses_areas = True

    def _calculate(self):
        image_width, image_height = self.image.size
        not_none = lambda x: x is not None
        # image_width and image_height are known to be defined.
        new_width = ifilter(not_none,
                            (self.width,
                             self.max_width,
                             image_width)
                            ).next()
        new_height = ifilter(not_none,
                             (self.height,
                              self.max_height,
                              image_height)
                             ).next()

        new_width = min(new_width, image_width)
        new_height = min(new_height, image_height)

        return new_width, new_height

    def _adjust(self):
        image_width, image_height = self.image.size
        new_width, new_height = self.calculate()

        if not self.areas:
            x1 = (image_width - new_width) / 2
            y1 = (image_height - new_height) / 2
        else:
            min_penalty = None
            optimal_coords = None

            for x in xrange(image_width - new_width + 1):
                for y in xrange(image_height - new_height + 1):
                    penalty = 0
                    for area in self.areas:
                        penalty += self._get_penalty(area, x, y,
                                                     new_width, new_height)
                        if min_penalty is not None and penalty > min_penalty:
                            break

                    if min_penalty is None or penalty < min_penalty:
                        min_penalty = penalty
                        optimal_coords = [(x, y)]
                    elif penalty == min_penalty:
                        optimal_coords.append((x, y))
            x1, y1 = optimal_coords[0]

        x2 = x1 + new_width
        y2 = y1 + new_height

        return self.image.crop((x1, y1, x2, y2))

    def _get_penalty(self, area, x1, y1, new_width, new_height):
        x2 = x1 + new_width
        y2 = y1 + new_height
        if area.x1 >= x1 and area.x2 <= x2 and area.y1 >= y1 and area.y2 <= y2:
            # The area is enclosed. No penalty
            penalty_area = 0
        elif area.x2 < x1 or area.x1 > x2 or area.y2 < y1 or area.y1 > y2:
            # The area is excluded. Penalty for the whole thing.
            penalty_area = area.area
        else:
            # Partial penalty.
            non_penalty_area = (min(area.x2 - x1, x2 - area.x1, area.width) *
                                min(area.y2 - y1, y2 - area.y1, area.height))
            penalty_area = area.area - non_penalty_area
        return penalty_area / area.priority


class Fill(Adjustment):
    """
    Crops the image to the requested ratio (using the same logic as
    :class:`.Crop` to protect :class:`~daguerre.models.Area` instances which
    are passed in), then resizes it to the actual requested dimensions. If
    ``width`` or ``height`` is ``None``, then the unspecified dimension will be
    allowed to expand up to ``max_width`` or ``max_height``, respectively.

    """
    uses_areas = True

    def _calculate(self):
        image_width, image_height = self.image.size
        # If there are no restrictions, just return the original dimensions.
        if self.height is None and self.width is None:
            return image_width, image_height

        image_ratio = float(image_width) / image_height

        if self.height is None:
            new_height = int(self.width / image_ratio)
            if self.max_height is not None:
                new_height = min(new_height, int(self.max_height))
            new_width = int(self.width)
        elif self.width is None:
            new_width = int(self.height * image_ratio)
            if self.max_width is not None:
                new_width = min(new_width, int(self.max_width))
            new_height = int(self.height)
        else:
            new_width = self.width
            new_height = self.height

        return new_width, new_height

    def _adjust(self):
        image_width, image_height = self.image.size
        new_width, new_height = self.calculate()

        image_ratio = float(image_width) / image_height
        new_ratio = float(new_width) / new_height

        if new_ratio > image_ratio:
            # New ratio is wider. Cut the height.
            crop_width = image_width
            crop_height = int(image_width / new_ratio)
        else:
            crop_width = int(image_height * new_ratio)
            crop_height = image_height

        new_image = Crop(self.image, width=crop_width, height=crop_height,
                         areas=self.areas).adjust()

        return Fit(new_image, width=new_width, height=new_height).adjust()


adjustments['fit'] = Fit
adjustments['crop'] = Crop
adjustments['fill'] = Fill


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

    def adjustment_for_path(self, storage_path):
        # Will raise IOError if the file doesn't exist or isn't a valid image.
        return self.adjustment_class(self._open_image(storage_path),
                                     **self.kwargs)

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
            adjustment = self.adjustment_for_path(storage_path)
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

    def adjustment_for_path(self, storage_path):
        # Will raise IOError if the file doesn't exist or isn't a valid image.
        im = self._open_image(storage_path)
        crop_area = self.get_crop_area()
        if crop_area is None:
            areas = self.get_areas()
        else:
            # Ignore areas if there is a valid crop, for now.
            # Maybe someday "crop" the areas and pass them in.
            areas = None
            im = im.crop((crop_area.x1, crop_area.y1,
                          crop_area.x2, crop_area.y2))

        kwargs = self.kwargs.copy()
        kwargs.pop('crop', None)

        return self.adjustment_class(im, areas=areas, **kwargs)

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
        adjustment = self.adjustment_for_path(self.storage_path)
        im = adjustment.adjust()

        creation_kwargs = {}
        for k, v in kwargs.iteritems():
            if k.endswith('__isnull'):
                creation_kwargs[k[:-len('__isnull')]] = None
            else:
                creation_kwargs[k] = v

        adjusted = AdjustedImage(**creation_kwargs)
        f = adjusted._meta.get_field('adjusted')

        format = (adjustment.format
                  if adjustment.format in KEEP_FORMATS else DEFAULT_FORMAT)
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
