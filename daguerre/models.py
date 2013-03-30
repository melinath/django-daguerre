from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import capfirst
from django.utils.encoding import smart_unicode
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Area(models.Model):
	"""Represents an area of an image. Can be used to specify a crop. Also used for priority-aware automated image cropping."""
	storage_path = models.CharField(max_length=300)
	
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
	
	def serialize(self):
		return dict((f.name, getattr(self, f.name))
					for f in self._meta.fields)

	def save(self, *args, **kwargs):
		"""
		If the adjusted image uses areas (e.g., fill and crop), clear cached adjusted images.
		
		"""
		from daguerre.utils.adjustments import adjustments
		slugs = [slug for slug, adjustment in adjustments.iteritems() if adjustment.uses_areas]
		AdjustedImage.objects.filter(storage_path__exact=self.storage_path, requested_adjustment__in=slugs).delete()
		super(Area, self).save(*args, **kwargs)
		
	def __unicode__(self):
		if self.name:
			name = self.name
		else:
			name = u"(%d, %d, %d, %d / %d)" % (self.x1, self.y1, self.x2, self.y2, self.priority)
		return u"%s for %s" % (name, self.storage_path)
	
	class Meta:
		ordering = ('priority',)

@receiver(post_delete, sender=Area)
def delete_adjusted_images(sender, **kwargs):
	from daguerre.utils.adjustments import adjustments
	slugs = [slug for slug, adjustment in adjustments.iteritems() if adjustment.uses_areas]
	AdjustedImage.objects.filter(storage_path__exact=kwargs['instance'].storage_path, requested_adjustment__in=slugs).delete()


def _adjustment_choice_iter():
	# By lazily importing the adjustments dict, we can prevent an import loop.
	from daguerre.utils.adjustments import adjustments
	for slug in adjustments:
		yield (slug, capfirst(slug))


class AdjustedImage(models.Model):
	"""Represents a "cached" managed image adjustment."""
	storage_path = models.CharField(max_length=300)
	adjusted = models.ImageField(height_field='height', width_field='width', upload_to='daguerre/adjusted/%Y/%m/%d/', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)

	width = models.PositiveIntegerField()
	height = models.PositiveIntegerField()

	requested_width = models.PositiveIntegerField(blank=True, null=True)
	requested_height = models.PositiveIntegerField(blank=True, null=True)
	requested_max_width = models.PositiveIntegerField(blank=True, null=True)
	requested_max_height = models.PositiveIntegerField(blank=True, null=True)
	requested_adjustment = models.CharField(max_length=255, choices=_adjustment_choice_iter())
	requested_crop = models.ForeignKey(Area, blank=True, null=True)

	def __unicode__(self):
		return u"(%s, %s) adjustment for %s" % (smart_unicode(self.requested_width), smart_unicode(self.requested_height), self.storage_path)
