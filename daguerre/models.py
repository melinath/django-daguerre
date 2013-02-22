from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import capfirst
from django.utils.encoding import smart_unicode


class Area(models.Model):
	"""Represents an area of an image. Can be used to specify a crop. Also used for priority-aware automated image cropping."""
	storage_path = models.CharField(max_length=300, db_index=True)
	
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
		unique_together = ('storage_path', 'x1', 'y1', 'x2', 'y2')


def _adjustment_choice_iter():
	# By lazily importing the adjustments dict, we can prevent an import loop.
	from daguerre.utils.adjustments import adjustments
	for slug in adjustments:
		yield (slug, capfirst(slug))


class AdjustedImage(models.Model):
	"""Represents a "cached" managed image adjustment."""
	storage_path = models.CharField(max_length=300, db_index=True)
	adjusted = models.ImageField(height_field='height', width_field='width', upload_to='daguerre/images/%Y/%m/%d/adjusted/', max_length=255)
	timestamp = models.DateTimeField(auto_now_add=True)

	width = models.PositiveIntegerField(db_index=True)
	height = models.PositiveIntegerField(db_index=True)

	requested_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_width = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_max_height = models.PositiveIntegerField(db_index=True, blank=True, null=True)
	requested_adjustment = models.CharField(db_index=True, max_length=255, choices=_adjustment_choice_iter())
	requested_crop = models.ForeignKey(Area, blank=True, null=True)

	def __unicode__(self):
		return u"(%s, %s) adjustment for %s" % (smart_unicode(self.requested_width), smart_unicode(self.requested_height), self.storage_path)
