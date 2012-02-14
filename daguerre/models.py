import mimetypes
import os
import itertools
from hashlib import sha1

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import capfirst
from django.utils.encoding import smart_str, smart_unicode
import Image as PILImage

from daguerre.cache import clear_cache, get_cache_key
from daguerre.validators import FileTypeValidator
from daguerre.utils import runmethod, methods


__all__ = ('Image', 'Area', 'AdjustedImage', 'ImageGallery', 'ImageGalleryOrder', 'ImageMetadata')


class Image(Entity):
	"""A basic image. Has a name, a unique slug, an image file, a timestamp, and width/height fields."""
	name = models.CharField(max_length=100)
	slug = models.SlugField(max_length=100, unique=True)
	
	image = models.ImageField(upload_to='assets/images/%Y/%m/%d', validators=[FileTypeValidator(['.jpg', '.gif', '.png'])], help_text="Allowed file types: .jpg, .gif, and .png", height_field='height', width_field='width', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	height = models.PositiveIntegerField()
	width = models.PositiveIntegerField()
	
	def save(self, *args, **kwargs):
		super(Image, self).save(*args, **kwargs)
	
	def delete(self, *args, **kwargs):
		super(Image, self).save(*args, **kwargs)
	
	def __unicode__(self):
		return self.name


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


class TemporaryImageFile(UploadedFile):
	"""HACK to allow setting of an AdjustedImage's image attribute with a generated (rather than uploaded) image file."""
	def __init__(self, name, image, format):
		if settings.FILE_UPLOAD_TEMP_DIR:
			file = NamedTemporaryFile(suffix='.upload', dir=settings.FILE_UPLOAD_TEMP_DIR)
		else:
			file = NamedTemporaryFile(suffix='.upload')
		image.save(file, format)
		content_type = "image/%s" % format.lower()
		# Should we even bother calculating the size?
		size = os.path.getsize(file.name)
		super(TemporaryImageFile, self).__init__(file, name, content_type, size)
	
	def temporary_file_path(self):
		return self.file.name
	
	def close(self):
		try:
			return self.file.close()
		except OSError, e:
			if e.errno != 2:
				# Means the file was moved or deleted before the tempfile
				# could unlink it. Still sets self.file.close_called and
				# calls self.file.file.close() before the exception
				raise


class AdjustedImageManager(models.Manager):
	def adjust_image(self, image, width=None, height=None, max_width=None, max_height=None, method='', crop=None):
		"""Makes an AdjustedImage instance for the requested parameters from the given Image."""
		image.image.seek(0)
		im = PILImage.open(image.image)
		format = im.format
		
		if crop is not None:
			im = im.crop((crop.x1, crop.y1, crop.x2, crop.y2))
			areas = None
		else:
			areas = image.areas.all()
		
		im = runmethod(method, im, width=width, height=height, max_width=max_width, max_height=max_height, areas=areas)
		
		adjusted = self.model(image=image, requested_width=width, requested_height=height, requested_max_width=max_width, requested_max_height=max_height, requested_method=method, requested_crop=crop)
		f = adjusted._meta.get_field('adjusted')
		ext = mimetypes.guess_extension('image/%s' % format.lower())
		
		# dot is included in ext.
		arg_prefix = get_cache_key(width, height, max_width, max_height, method)[::4]
		filename = "%s_%s%s" % (arg_prefix, image.slug, ext)
		filename = f.generate_filename(adjusted, filename)
		
		temp = TemporaryImageFile(filename, im, format)
		
		adjusted.adjusted = temp
		# Try to handle race conditions gracefully.
		try:
			adjusted = self.get(image=image, requested_width=width, requested_height=height, requested_max_width=max_width, requested_max_height=max_height, requested_method=method, requested_crop=crop)
		except self.model.DoesNotExist:
			adjusted.save()
		else:
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
	adjusted = models.ImageField(height_field='height', width_field='width', upload_to='assets/images/%Y/%m/%d/adjusted/', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)
	
	width = models.PositiveIntegerField(db_index=True)
	height = models.PositiveIntegerField(db_index=True)
	
	requested_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_method = models.CharField(db_index=True, max_length=255, choices=[(slug, capfirst(slug)) for slug in methods])
	requested_crop = models.ForeignKey(Area, blank=True, null=True)
	
	def delete(self, *args, **kwargs):
		super(AdjustedImage, self).delete(*args, **kwargs)
		clear_cache(self.image.slug, self.requested_width, self.requested_height, self.requested_max_width, self.requested_max_height, self.requested_method, getattr(self.requested_crop, 'name', None))
	
	def __unicode__(self):
		return u"(%s, %s) adjustment for %s" % (smart_unicode(self.requested_width), smart_unicode(self.requested_height), self.image)
	
	class Meta:
		unique_together = ('image', 'requested_width', 'requested_height', 'requested_max_width', 'requested_max_height', 'requested_method')


class ImageMetadata(Entity):
	"""Contains image metadata which is not central to the concept of an Image."""
	image = models.OneToOneField(Image, related_name='metadata')
	caption = models.TextField(help_text='May contain HTML', blank=True)
	credit = models.CharField(max_length=100, blank=True)
	artist = models.ForeignKey(getattr(settings, 'PHILO_PERSON_MODULE', 'auth.User'), blank=True, null=True)
	creation_date = models.DateField(blank=True, null=True, help_text="The date that the image was created, not the date it was added to the system.")
	
	def __unicode__(self):
		return u"Metadata for %s" % self.image


class ImageGalleryOrder(models.Model):
	gallery = models.ForeignKey('ImageGallery')
	image = models.ForeignKey(Image)
	order = models.PositiveIntegerField(blank=True, null=True)
	
	class Meta:
		unique_together = ('image', 'gallery')
		ordering = ('order',)


class ImageGallery(Entity):
	"""Represents a gallery of images."""
	name = models.CharField(max_length=75)
	images = models.ManyToManyField(Image, through=ImageGalleryOrder)
	
	@property
	def gallery(self):
		"""Ordinarily items with no order (i.e. order of `None`) would be placed before everything else. This property returns an iterator that places those items at the end. TODO: write a custom iterator that goes over a single ordered queryset and simply saves the items with no order for later."""
		if not hasattr(self, '_gallery'):
			unordered = Image.objects.filter(imagegalleryorder__order__isnull=True, imagegalleryorder__gallery=self)
			ordered = self.images.filter(imagegalleryorder__order__isnull=False, imagegalleryorder__gallery=self).order_by('imagegalleryorder__order')
			self._gallery = itertools.chain(ordered, unordered)
		self._gallery, gallery = itertools.tee(self._gallery)
		return gallery
	
	@property
	def first(self):
		"""Returns the first item in the gallery. This is necessary because the iterator returned by :prop:`gallery` can't be sliced or indexed."""
		gallery = self.gallery
		try:
			return gallery.next()
		except StopIteration:
			return None
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		verbose_name_plural = 'Image Galleries'