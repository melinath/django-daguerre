from __future__ import division
from six.moves import xrange

from daguerre.utils import exif_aware_resize, exif_aware_size

try:
    from PIL import Image
except ImportError:
    import Image


class AdjustmentRegistry(object):
    def __init__(self):
        self._registry = {}
        self._default = None

    def register(self, cls):
        self._registry[cls.__name__.lower()] = cls
        return cls

    def __getitem__(self, key):
        return self._registry[key]

    def get(self, key, default=None):
        return self._registry.get(key, default)

    def __contains__(self, item):
        return item in self._registry

    def items(self):
        return self._registry.items()


registry = AdjustmentRegistry()


class Adjustment(object):
    """
    Base class for all adjustments which can be carried out on an image. The
    adjustment itself represents a set of parameters, which can then be
    applied to images (taking areas into account if applicable).

    Adjustment subclasses need to define two methods: :meth:`calculate` and
    :meth:`adjust`. If the method doesn't use areas, you can set the
    ``uses_areas`` attribute on the method to ``False`` to optimize
    adjustment.

    :param kwargs: The requested kwargs for the adjustment. The keys must
                   be in :attr:`parameters` or the adjustment is invalid.

    """
    #: Accepted parameters for this adjustment - for example, ``"width"``,
    #: ``"height"``, ``"color"``, ``"unicorns"``, etc.
    parameters = ()

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for key in kwargs:
            if key not in self.parameters:
                raise ValueError('Parameter "{0}" not accepted by {1}.'
                                 ''.format(key, self.__class__.__name__))

    def calculate(self, dims, areas=None):
        """
        Calculates the dimensions of the adjusted image without actually
        manipulating the image. By default, just returns the given dimensions.

        :param dims: ``(width, height)`` tuple of the current image
                     dimensions.
        :param areas: iterable of :class:`.Area` instances to be considered in
                      calculating the adjustment.

        """
        return dims
    calculate.uses_areas = False

    def adjust(self, image, areas=None):
        """
        Manipulates and returns the image. Must be implemented by subclasses.

        :param image: PIL Image which will be adjusted.
        :param areas: iterable of :class:`.Area` instances to be considered in
                      performing the adjustment.

        """
        raise NotImplementedError


@registry.register
class Fit(Adjustment):
    """
    Resizes an image to fit entirely within the given dimensions
    without cropping and maintaining the width/height ratio.

    If neither width nor height is specified, this adjustment will simply
    return a copy of the image.

    """
    parameters = ('width', 'height')

    def calculate(self, dims, areas=None):
        image_width, image_height = dims
        width, height = self.kwargs.get('width'), self.kwargs.get('height')

        if width is None and height is None:
            return image_width, image_height

        image_ratio = float(image_width) / image_height

        if height is None:
            # Constrain first by width, then by max_height.
            new_width = int(width)
            new_height = int(round(new_width / image_ratio))
        elif width is None:
            # Constrain first by height, then by max_width.
            new_height = int(height)
            new_width = int(round(new_height * image_ratio))
        else:
            # Constrain strictly by both dimensions.
            width, height = int(width), int(height)
            new_width = int(min(width, round(height * image_ratio)))
            new_height = int(min(height, round(width / image_ratio)))

        return new_width, new_height
    calculate.uses_areas = False

    def adjust(self, image, areas=None):
        image_width, image_height = exif_aware_size(image)
        new_width, new_height = self.calculate((image_width, image_height))

        if (new_width, new_height) == (image_width, image_height):
            return image.copy()

        # Choose a resize filter based on whether
        # we're upscaling or downscaling.
        if new_width < image_width:
            f = Image.ANTIALIAS
        else:
            f = Image.BICUBIC

        return exif_aware_resize(image, (new_width, new_height), f)
    adjust.uses_areas = False


@registry.register
class Crop(Adjustment):
    """
    Crops an image to the given width and height, without scaling it.
    :class:`~daguerre.models.Area` instances which are passed in will be
    protected as much as possible during the crop.

    """
    parameters = ('width', 'height')

    def calculate(self, dims, areas=None):
        image_width, image_height = dims
        width, height = self.kwargs.get('width'), self.kwargs.get('height')
        # image_width and image_height are known to be defined.
        new_width = int(width) if width is not None else image_width
        new_height = int(height) if height is not None else image_height

        new_width = min(new_width, image_width)
        new_height = min(new_height, image_height)

        return new_width, new_height
    calculate.uses_areas = False

    def adjust(self, image, areas=None):
        image_width, image_height = exif_aware_size(image)
        new_width, new_height = self.calculate((image_width, image_height))

        if (new_width, new_height) == (image_width, image_height):
            return image.copy()

        if not areas:
            x1 = int((image_width - new_width) / 2)
            y1 = int((image_height - new_height) / 2)
        else:
            min_penalty = None
            optimal_coords = None

            for x in xrange(image_width - new_width + 1):
                for y in xrange(image_height - new_height + 1):
                    penalty = 0
                    for area in areas:
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

        return image.crop((x1, y1, x2, y2))

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


@registry.register
class RatioCrop(Crop):
    """
    Crops an image to the given aspect ratio, without scaling it.
    :class:`~daguerre.models.Area` instances which are passed in will be
    protected as much as possible during the crop.

    """
    #: ``ratio`` should be formatted as ``"<width>:<height>"``
    parameters = ('ratio',)

    def calculate(self, dims, areas=None):
        image_width, image_height = dims
        image_ratio = float(image_width) / image_height
        ratio_str = self.kwargs.get('ratio')

        if ratio_str is None:
            return image_width, image_height

        width, height = ratio_str.split(':')
        ratio = float(width) / float(height)

        if ratio > image_ratio:
            # New ratio is wider. Cut the height.
            new_width = image_width
            new_height = int(image_width / ratio)
        else:
            new_width = int(image_height * ratio)
            new_height = image_height

        return new_width, new_height
    calculate.uses_areas = False


@registry.register
class NamedCrop(Adjustment):
    """
    Crops an image to the given named area, without scaling it.
    :class:`~daguerre.models.Area` instances which are passed in will be
    protected as much as possible during the crop.

    If no area with the given name exists, this adjustment is a no-op.

    """
    parameters = ('name',)

    def calculate(self, dims, areas=None):
        image_width, image_height = dims

        if not areas:
            return image_width, image_height

        for area in areas:
            if area.name == self.kwargs['name']:
                break
        else:
            return image_width, image_height

        return area.width, area.height

    def adjust(self, image, areas=None):
        image_width, image_height = exif_aware_size(image)

        if not areas:
            return image.copy()

        for area in areas:
            if area.name == self.kwargs['name']:
                break
        else:
            return image.copy()

        return image.crop((area.x1, area.y1,
                           area.x2, area.y2))


@registry.register
class Fill(Adjustment):
    """
    Crops the image to the requested ratio (using the same logic as
    :class:`.Crop` to protect :class:`~daguerre.models.Area` instances which
    are passed in), then resizes it to the actual requested dimensions. If
    ``width`` or ``height`` is not given, then the unspecified dimension will
    be allowed to expand up to ``max_width`` or ``max_height``, respectively.

    """
    parameters = ('width', 'height', 'max_width', 'max_height')

    def calculate(self, dims, areas=None):
        image_width, image_height = dims
        width, height = self.kwargs.get('width'), self.kwargs.get('height')

        if width is None and height is None:
            # No restrictions: return original dimensions.
            return image_width, image_height

        max_width = self.kwargs.get('max_width')
        max_height = self.kwargs.get('max_height')
        image_ratio = float(image_width) / image_height

        if width is None:
            new_height = int(height)
            new_width = int(new_height * image_ratio)
            if max_width is not None:
                new_width = min(new_width, int(max_width))
        elif height is None:
            new_width = int(width)
            new_height = int(new_width / image_ratio)
            if max_height is not None:
                new_height = min(new_height, int(max_height))
        else:
            new_width = int(width)
            new_height = int(height)

        return new_width, new_height
    calculate.uses_areas = False

    def adjust(self, image, areas=None):
        image_width, image_height = exif_aware_size(image)
        new_width, new_height = self.calculate((image_width, image_height))

        if (new_width, new_height) == (image_width, image_height):
            return image.copy()

        ratiocrop = RatioCrop(ratio="{0}:{1}".format(new_width, new_height))
        new_image = ratiocrop.adjust(image, areas=areas)

        fit = Fit(width=new_width, height=new_height)
        return fit.adjust(new_image)
