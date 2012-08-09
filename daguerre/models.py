import datetime
import mimetypes
import os
import itertools
from hashlib import sha1

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import capfirst
from django.utils.encoding import smart_str, smart_unicode
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.validators import FileTypeValidator
from daguerre.utils.adjustments import get_adjustment_class, adjustments, DEFAULT_ADJUSTMENT


class ImageManager(models.Manager):
	def for_storage_path(self, storage_path):
		"""
		Returns an :class:`Image` for the given ``storage_path``, creating it
		if necessary. If more than one :class:`Image` exists (which could
		happen due to a race condition in image creation) then the first
		instance encountered is returned.

		"""
		images = self.filter(image=storage_path)
		try:
			image = images[0]
		except IndexError:
			try:
				im_file = default_storage.open(storage_path)
			except IOError:
				raise self.model.DoesNotExist("Path could not be opened.")

			try:
				PILImage.open(im_file)
			except IOError:
				raise self.model.DoesNotExist("Path does not point to a valid image file.")

			image = self.model()
			image.image = storage_path
			image.save()
		return image


class Image(models.Model):
	"""A basic image. Has a name, an image file, a timestamp, and width/height fields."""
	name = models.CharField(max_length=100, blank=True)
	
	image = models.ImageField(upload_to='daguerre/images/%Y/%m/%d', validators=[FileTypeValidator(['.jpg', '.gif', '.png'])], help_text="Allowed file types: .jpg, .gif, and .png", height_field='height', width_field='width', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	height = models.PositiveIntegerField()
	width = models.PositiveIntegerField()

	objects = ImageManager()
	
	def __unicode__(self):
		return self.name or self.image.name


class Area(models.Model):
	"""Represents an area of an image. Can be used to specify a crop. Also used for priority-aware automated image cropping."""
	image = models.ForeignKey(Image, related_name="areas")
	
	x1 = models.PositiveIntegerField(validators=[MinValueValidator(0)])
	y1 = models.PositiveIntegerField(validators=[MinValueValidator(0)])
	x2 = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	y2 = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	
	name = models.CharField(max_length=20, blank=True)
	priority = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=3)
	
	@property
	def area(self):
		if self.x1 is None or self.y1 is None or self.x2 is None or self.y2 is None:
			return None
		return self.width * self.height
	
	@property
	def width(self):
		return self.x2 - self.x1
	
	@property
	def height(self):
		return self.y2 - self.y1
	
	def clean_fields(self, exclude=None):
		errors = {}
		
		if exclude is None:
			exclude = []
		
		try:
			super(Area, self).clean_fields(exclude)
		except ValidationError, e:
			errors.update(e.message_dict)
		
		if 'x2' not in exclude and self.x2 > self.image.width:
			errors.setdefault('x2', []).append(u"Ensure that this value is less than or equal to %d." % self.image.width)
		if 'y2' not in exclude and self.y2 > self.image.height:
			errors.setdefault('y2', []).append(u"Ensure that this value is less than or equal to %d." % self.image.height)
		
		if errors:
			raise ValidationError(errors)
	
	def clean(self):
		errors = []
		if self.x1 and self.x2 and self.x1 >= self.x2:
			errors.append("X1 must be less than X2.")
		if self.y1 and self.y2 and self.y1 >= self.y2:
			errors.append("Y1 must be less than Y2.")
		if errors:
			raise ValidationError(errors)
	
	def __unicode__(self):
		if self.name:
			name = self.name
		else:
			name = u"(%d, %d, %d, %d / %d)" % (self.x1, self.y1, self.x2, self.y2, self.priority)
		return u"%s for %s" % (name, self.image)
	
	class Meta:
		ordering = ('priority',)
		unique_together = ('image', 'x1', 'y1', 'x2', 'y2')


class AdjustedImageManager(models.Manager):
	def adjust(self, image, width=None, height=None, max_width=None, max_height=None, adjustment=DEFAULT_ADJUSTMENT, crop=None):
		"""
		Fetches or creates an :class:`~AdjustedImage` instance for the requested parameters.

		:param image: The :class:`~Image` instance which is to be adjusted.
		:param integers width, height, max_width, max_height: The requested dimensions for the adjusted image.
		:param crop: The name of an :class:`~Area` associated with the :class:`Image`; if the crop exists, it will be applied before any other adjustments or calculations.

		"""

		adjusted_image_kwargs = {
			'image': image,
			'requested_adjustment': adjustment,
		}

		adjustment_class = get_adjustment_class(adjustment)
		adjustment = adjustment_class.from_image(image, crop=crop, width=width, height=height, max_width=max_width, max_height=max_height)

		adjusted_image_kwargs.update({
			'requested_width': width,
			'requested_height': height,
			'requested_max_width': max_width,
			'requested_max_height': max_height,
			'requested_crop': adjustment._crop_area
		})

		adjusted_image_query_kwargs = dict(("%s__isnull" % k, True) if v is None else (k, v) for k, v in adjusted_image_kwargs.iteritems())

		try:
			adjusted = self.get(**adjusted_image_query_kwargs)
		except self.model.DoesNotExist:
			adjusted = self.model(**adjusted_image_kwargs)

			im = adjustment.adjust()
			f = adjusted._meta.get_field('adjusted')
			ext = mimetypes.guess_extension(adjustment.mimetype)

			filename = ''.join((sha1(''.join(unicode(arg) for arg in (width, height, max_width, max_height, adjustment, crop, image.image.name, datetime.datetime.now().isoformat()))).hexdigest()[::2], ext))
			filename = f.generate_filename(adjusted, filename)

			temp = NamedTemporaryFile()
			im.save(temp, format=adjustment.format)
			adjusted.adjusted = File(temp, name=filename)
			# Try to handle race conditions gracefully.
			try:
				adjusted = self.get(**adjusted_image_query_kwargs)
			except self.model.DoesNotExist:
				adjusted.save()
			finally:
				temp.close()
		return adjusted


class AdjustedImage(models.Model):
	"""Represents a "cached" managed image adjustment."""
	#SCALE = 'scale'
	#CROP = 'crop'
	#SEAM = 'seam'
	#SCALE_CROP = 'scale+crop'
	objects = AdjustedImageManager()
	
	image = models.ForeignKey(Image)
	adjusted = models.ImageField(height_field='height', width_field='width', upload_to='daguerre/images/%Y/%m/%d/adjusted/', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	width = models.PositiveIntegerField(db_index=True)
	height = models.PositiveIntegerField(db_index=True)
	
	requested_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_adjustment = models.CharField(db_index=True, max_length=255, choices=[(slug, capfirst(slug)) for slug in adjustments])
	requested_crop = models.ForeignKey(Area, blank=True, null=True)
	
	def __unicode__(self):
		return u"(%s, %s) adjustment for %s" % (smart_unicode(self.requested_width), smart_unicode(self.requested_height), self.image)
	
	class Meta:
		unique_together = ('image', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_adjustment')
