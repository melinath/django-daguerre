from itertools import ifilter

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import QueryDict
try:
	from PIL import Image
except ImportError:
	import Image

from daguerre.utils import make_security_hash, AdjustmentInfoDict


adjustments = {}
DEFAULT_ADJUSTMENT = 'fit'
QUERY_PARAMS = {
	'width': 'w',
	'height': 'h',
	'max_width': 'max_w',
	'max_height': 'max_h',
	'adjustment': 'a',
	'security': 's',
	'crop': 'c'
}


def get_adjustment_class(slug):
	"""Instantiates and returns the adjustment registered as ``slug``, or the default adjustment if no matching adjustment is found. The remaining arguments are passed directly to the adjustment class to create the instance."""
	try:
		return adjustments[slug]
	except KeyError:
		return adjustments[DEFAULT_ADJUSTMENT]


class Adjustment(object):
	"""
	Base class for all adjustments which can be carried out on an image. Each adjustment has two stages: calculating the new image dimensions, and carrying out the adjustment.

	:param image: A PIL Image instance which is to be adjusted.
	:param width, height, max_width, max_height: The requested dimensions for the adjusted image.
	:param areas: :class:`~Area` instances representing protected areas for the adjustment.

	"""
	def __init__(self, image, width=None, height=None, max_width=None, max_height=None, areas=None):
		self.image = image
		self.format = self.image.format
		self.mimetype = None if self.format is None else "image/%s" % self.format.lower()

		self.areas = areas

		self.width = width
		self.height = height
		self.max_width = max_width
		self.max_height = max_height

	@classmethod
	def from_image(cls, image, crop=None, areas=None, **kwargs):
		"""Generate an adjusted image based on an :class:`~Image` instance rather than a straight PIL image. Essentially adds a little sugar on top."""
		im_file = default_storage.open(image.image.name)
		pil_image = Image.open(im_file)
		area = None
		if crop is not None:
			try:
				area = image.areas.get(name=crop)
			except ObjectDoesNotExist:
				crop = None
			else:
				# For now, just ignore all the areas if there is a
				# valid crop.  Technically, it would probably be
				# better to "crop" the areas as well.
				areas = None
				pil_image = pil_image.crop((area.x1,
											area.y1,
											area.x2,
											area.y2))
		
		if areas is None and crop is None:
			areas = image.areas.all()

		instance = cls(pil_image, areas=areas, **kwargs)
		instance._image = image
		instance._crop = crop
		instance._crop_area = area
		instance._storage_path = image.image.name
		return instance

	def calculate(self):
		"""Calculates the dimensions of the adjusted image without actually manipulating the image."""
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

	@property
	def querydict(self):
		"""Returns a querydict for this adjustment."""
		if not hasattr(self, '_querydict'):
			qd = QueryDict('', mutable=True)
			for adjustment, cls in adjustments.iteritems():
				if cls == self.__class__:
					break
			else:
				raise ValueError("Unregistered adjustment.")

			storage_path = self._storage_path
			security = make_security_hash(storage_path, self.width, self.height, self.max_width, self.max_height, adjustment, self._crop)

			qd[QUERY_PARAMS['adjustment']] = adjustment
			qd[QUERY_PARAMS['security']] = security
			for attr in ('width', 'height', 'max_width', 'max_height'):
				value = getattr(self, attr)
				if value is not None:
					qd[QUERY_PARAMS[attr]] = value
			if self._crop is not None:
				qd[QUERY_PARAMS['crop']] = self._crop
			self._querydict = qd
		return self._querydict

	@property
	def url(self):
		"""Returns a url for the adjusted image. This is only available for adjustments generated from an :class:`~Image`."""
		if not hasattr(self, '_image'):
			raise AttributeError
		return u"%s?%s" % (reverse('daguerre_adjusted_image_redirect', kwargs={'storage_path': self._storage_path}), self.querydict.urlencode())

	@property
	def ajax_url(self):
		"""Returns a url which can be used to fetch information about this adjustment via ajax. This is only available for adjustments generated from an :class:`~Image`."""
		if not hasattr(self, '_image'):
			raise AttributeError
		querydict = self.querydict.copy()
		querydict.pop(QUERY_PARAMS['security'])
		return u"%s?%s" % (reverse('daguerre_ajax_adjustment_info', kwargs={'storage_path': self._storage_path}), querydict.urlencode())

	def info_dict(self):
		"""
		Returns an information dictionary for the adjusted image without actually running the adjustment. The available information is:

		* format: image mimetype.
		* ident: storage path for the original image.
		* width, height: width/height of the resized image.
		* url: url for the resized image file.
		* ajax_url: url to get this information via ajax.
		* requested: a dictionary of information regarding the request. Contains keys for width, height, max_width, max_height, and crop.

		This method is only available from adjustments instantiated from an :class:`~Image`.

		"""
		if not hasattr(self, '_image'):
			raise AttributeError
		return AdjustmentInfoDict({
			'format': self.format,
			'ident': self._storage_path,
			'width': self.calculate()[0],
			'height': self.calculate()[1],
			'requested': {
				'width': self.width,
				'height': self.height,
				'max_width': self.max_width,
				'max_height': self.max_height,
				'crop': self._crop
			},
			'url': self.url,
			'ajax_url': self.ajax_url
		})


class Fit(Adjustment):
	"""
	Resizes an image to fit entirely within the given dimensions without cropping and maintaining the width/height ratio.

	Rather than constraining an image to a specific width and height, ``width`` or ``height`` may be given as ``None``, in which case the image can expand in the unspecified direction up to ``max_width`` or ``max_height``, respectively, or indefinitely if the relevant dimension is not specified.

	If neither width nor height is specified, this adjustment will simply return a copy of the image.

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

		# Choose a resize filter based on whether we're upscaling or downscaling.
		if new_width < image_width:
			f = Image.ANTIALIAS
		else:
			f = Image.BICUBIC
		return self.image.resize((new_width, new_height), f)



adjustments['fit'] = Fit


class Crop(Adjustment):
	"""
	Crops an image to the given width and height, without scaling it. :class:`~daguerre.models.Area` instances which are passed in will be protected as much as possible during the crop. If ``width`` or ``height`` is not specified, the image may grow up to ``max_width`` or ``max_height`` respectively in the unspecified direction before being cropped.

	"""
	def _calculate(self):
		image_width, image_height = self.image.size
		not_none = lambda x: x is not None
		# image_width and image_height are known to be defined.
		new_width = ifilter(not_none, (self.width, self.max_width, image_width)).next()
		new_height = ifilter(not_none, (self.height, self.max_height, image_height)).next()

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
						penalty += self._get_penalty(area, x, y, new_width, new_height)
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
			penalty_area = area.area - (min(area.x2 - x1, x2 - area.x1, area.width) * min(area.y2 - y1, y2 - area.y1, area.height))
		return penalty_area / area.priority


adjustments['crop'] = Crop


class Fill(Adjustment):
	"""
	Crops the image to the requested ratio (using the same logic as :class:`.Crop` to protect :class:`~daguerre.models.Area` instances which are passed in), then resizes it to the actual requested dimensions. If ``width`` or ``height`` is ``None``, then the unspecified dimension will be allowed to expand up to ``max_width`` or ``max_height``, respectively.

	"""
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

		new_image = Crop(self.image, width=crop_width, height=crop_height, areas=self.areas).adjust()

		return Fit(new_image, width=new_width, height=new_height).adjust()


adjustments['fill'] = Fill
