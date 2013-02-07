import datetime
import mimetypes

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.utils.datastructures import SortedDict
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.models import Image, Area, AdjustedImage
from daguerre.utils import AdjustmentInfoDict, make_hash
from daguerre.utils.adjustments import DEFAULT_ADJUSTMENT, get_adjustment_class


class AdjustmentHelper(object):
	int_params = set(('width', 'height', 'max_width', 'max_height'))
	param_map = {
		'width': 'w',
		'height': 'h',
		'max_width': 'max_w',
		'max_height': 'max_h',
		'adjustment': 'a',
		'security': 's',
		'crop': 'c'
	}

	def __init__(self, image_or_storage_path, **kwargs):
		if isinstance(image_or_storage_path, Image):
			self._image = image_or_storage_path
			self.storage_path = self._image.storage_path
		else:
			self.storage_path = image_or_storage_path

		self.kwargs = kwargs
		self.adjustment = kwargs.pop('adjustment', DEFAULT_ADJUSTMENT)

	def get_image(self):
		if not hasattr(self, '_image'):
			try:
				self._image = Image.objects.for_storage_path(self.storage_path)
			except Image.DoesNotExist:
				self._image = None
		return self._image

	def get_areas(self):
		if not hasattr(self, '_areas'):
			image = self.get_image()
			if image is None:
				self._areas = Area.objects.none()
			else:
				self._areas = image.areas.all()
		return self._areas

	def get_crop_area(self):
		if not hasattr(self, '_crop_area'):
			area = None
			if 'crop' in self.kwargs:
				image = self.get_image()
				if image is not None:
					try:
						area = self.get_areas().get(name=self.kwargs['crop'])
					except Area.DoesNotExist:
						pass
			self._crop_area = area
		return self._crop_area

	def get_query_kwargs(self):
		if not hasattr(self, '_query_kwargs'):
			query_kwargs = {
				'requested_adjustment': self.adjustment,
				'storage_path': self.storage_path,
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
		kwargs = self.kwargs.copy()
		kwargs['adjustment'] = self.adjustment

		if secure:
			kwargs['security'] = self.make_security_hash(kwargs)

		for k, v in kwargs.iteritems():
			qd[self.param_map[k]] = v

		return qd

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
		# Will raise IOError if the file doesn't exist or isn't an image.
		im_file = default_storage.open(image.image.name)
		pil_image = PILImage.open(im_file)
		crop_area = self.get_crop_area()
		if crop_area is None:
			areas = self.get_areas()
		else:
			# Ignore areas if there is a valid crop, for now.
			# Maybe someday "crop" the areas and pass them in.
			areas = None
			pil_image = pil_image.crop((crop_area.x1, crop_area.y1, crop_area.x2, crop_area.y2))

		adjustment_class = get_adjustment_class(self.adjustment)
		return adjustment_class(pil_image, areas=areas, **self.kwargs)

	def info_dict(self, fetch_first=True):
		"""
		Main method. The AdjustmentHelper should be able to calculate
		an appropriate info dict with minimal effort just by running
		this method.

		"""
		kwargs = self.get_query_kwargs()

		# First try to fetch a previously-adjusted image and return its info
		# dict. We also have the option of skipping this step.
		if fetch_first:
			try:
				adjusted = AdjustedImage.objects.filter(**kwargs)[:1][0]
			except IndexError:
				pass
			else:
				return adjusted.info_dict()

		# If that fails, try to do a lazy adjustment based on the image.
		image = self.get_image()
		if image is not None:
			try:
				adjustment = self.adjustment_for_image(image)
			except IOError:
				pass
			else:
				return AdjustmentInfoDict({
					'format': adjustment.format,
					'ident': self.storage_path,
					'width': adjustment.calculate()[0],
					'height': adjustment.calculate()[1],
					'requested': self.kwargs.copy(),
					'url': u"{0}?{1}".format(reverse('daguerre_adjusted_image_redirect', kwargs={'storage_path': self.storage_path}), self.to_querydict(secure=True).urlencode()),
					'ajax_url': u"{0}?{1}".format(reverse('daguerre_ajax_adjustment_info', kwargs={'storage_path': self.storage_path}), self.to_querydict(secure=False).urlencode()),
				})
		return AdjustmentInfoDict()

	def adjust(self):
		# May raise IOError or Image.DoesNotExist.

		# First try to fetch a version that already exists.
		kwargs = self.get_query_kwargs()
		try:
			return AdjustedImage.objects.filter(**kwargs)[:1][0]
		except IndexError:
			pass

		# If that fails, try to create one from the image.
		image = self.get_image()
		if image is None:
			raise Image.DoesNotExist

		# Raises IOError if something goes wrong.
		adjustment = self.adjustment_for_image(image)

		creation_kwargs = {}
		for k, v in kwargs.iteritems():
			if k.endswith('__isnull'):
				creation_kwargs[k[:-len('__isnull')]] = None
			else:
				creation_kwargs[k] = v

		adjusted = AdjustedImage(**creation_kwargs)
		im = adjustment.adjust()
		f = adjusted._meta.get_field('adjusted')
		ext = mimetypes.guess_extension(adjustment.mimetype)

		args = (unicode(creation_kwargs), datetime.datetime.now().isoformat())
		filename = ''.join((make_hash(*args, step=2), ext))
		filename = f.generate_filename(adjusted, filename)

		temp = NamedTemporaryFile()
		im.save(temp, format=adjustment.format)
		adjusted.adjusted = File(temp, name=filename)
		# Try to handle race conditions gracefully.
		try:
			return AdjustedImage.objects.filter(**kwargs)[:1][0]
		except IndexError:
			adjusted.save()
		finally:
			temp.close()
		return adjusted