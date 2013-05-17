from itertools import ifilter

try:
    from PIL import Image
except ImportError:
    import Image


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
