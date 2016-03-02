import operator

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from six.moves import reduce

from daguerre.adjustments import registry


class Area(models.Model):
    """
    Represents an area of an image. Can be used to specify a crop. Also used
    for priority-aware automated image cropping.

    """
    storage_path = models.CharField(max_length=300)

    x1 = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    y1 = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    x2 = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    y2 = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    name = models.CharField(max_length=20, blank=True)
    priority = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                           default=3)

    @property
    def area(self):
        if None in (self.x1, self.y1, self.x2, self.y2):
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
        except ValidationError as e:
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

    def __unicode__(self):
        if self.name:
            name = self.name
        else:
            name = u"(%d, %d, %d, %d / %d)" % (self.x1, self.y1, self.x2,
                                               self.y2, self.priority)
        return u"%s for %s" % (name, self.storage_path)

    class Meta:
        ordering = ('priority',)


@receiver(post_save, sender=Area)
@receiver(post_delete, sender=Area)
def delete_adjusted_images(sender, **kwargs):
    """
    If an Area is deleted or changed, delete all AdjustedImages for the
    Area's storage_path which have area-using adjustments.

    """
    storage_path = kwargs['instance'].storage_path
    qs = AdjustedImage.objects.filter(storage_path=storage_path)
    slug_qs = [models.Q(requested__contains=slug)
               for slug, adjustment in registry.items()
               if getattr(adjustment.adjust, 'uses_areas', True)]
    if slug_qs:
        qs = qs.filter(reduce(operator.or_, slug_qs))

    qs.delete()


class AdjustedImage(models.Model):
    """Represents a managed image adjustment."""
    storage_path = models.CharField(max_length=200)
    # The image name is a 20-character hash, so the max length with a 4-char
    # extension (jpeg) is 45.
    adjusted = models.ImageField(upload_to='daguerre/%Y/%m/%d/',
                                 max_length=45)
    requested = models.CharField(max_length=100)

    class Meta:
        index_together = [['requested', 'storage_path'], ]

    def __unicode__(self):
        return u"{0}: {1}".format(self.storage_path, self.requested)
