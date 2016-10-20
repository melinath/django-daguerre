# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import hashlib
import operator
import warnings
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.encoding import force_bytes, python_2_unicode_compatible
from six.moves import reduce

from daguerre.adjustments import registry

# The default image path where the images will be saved to. Can be overriden by
# defining the DAGUERRE_ADJUSTED_IMAGE_PATH setting in the project's settings.
# Example: DAGUERRE_ADJUSTED_IMAGE_PATH = 'img'
DEFAULT_ADJUSTED_IMAGE_PATH = 'dg'


@python_2_unicode_compatible
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

    def __str__(self):
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


def upload_to(instance, filename):
    """
    Construct the directory path where the adjusted images will be saved to
    using the MD5 hash algorithm.

    Can be customized using the DAGUERRE_PATH setting set in the project's
    settings. If left unspecified, the default value will be used, i.e. 'dg'.
    WARNING: The maximum length of the specified string is 13 characters.

    Example:
    * Default: dg/ce/2b/7014c0bdbedea0e4f4bf.jpeg
    * DAGUERRE_PATH = 'img': img/ce/2b/7014c0bdbedea0e4f4bf.jpeg

    Known issue:
    * If the extracted hash string is 'ad', ad blockers will block the image.
      All occurrences of 'ad' will be replaced with 'ag' since the MD5 hash
      produces letters from 'a' to 'f'.
    """

    image_path = getattr(
        settings, 'DAGUERRE_ADJUSTED_IMAGE_PATH', DEFAULT_ADJUSTED_IMAGE_PATH)

    if len(image_path) > 13:
        msg = ('The DAGUERRE_PATH value is more than 13 characters long! '
               'Falling back to the default '
               'value: "{}".'.format(DEFAULT_ADJUSTED_IMAGE_PATH))
        warnings.warn(msg)
        image_path = DEFAULT_ADJUSTED_IMAGE_PATH

    # Avoid TypeError on Py3 by forcing the string to bytestring
    # https://docs.djangoproject.com/en/dev/_modules/django/contrib/auth/hashers/
    # https://github.com/django/django/blob/master/django/contrib/auth/hashers.py#L524
    str_for_hash = force_bytes('{} {}'.format(filename, datetime.utcnow()))
    # Replace all occurrences of 'ad' with 'ag' to avoid ad blockers
    hash_for_dir = hashlib.md5(str_for_hash).hexdigest().replace('ad', 'ag')
    return '{0}/{1}/{2}/{3}'.format(
        image_path, hash_for_dir[0:2], hash_for_dir[2:4], filename)


@python_2_unicode_compatible
class AdjustedImage(models.Model):
    """Represents a managed image adjustment."""
    storage_path = models.CharField(max_length=200)
    # The image name is a 20-character hash, so the max length with a 4-char
    # extension (jpeg) is 45. The maximum length of the
    # DAGUERRE_ADJUSTED_IMAGE_PATH string is 13.
    adjusted = models.ImageField(upload_to=upload_to,
                                 max_length=45)
    requested = models.CharField(max_length=100)

    class Meta:
        index_together = [['requested', 'storage_path'], ]

    def __str__(self):
        return u"{0}: {1}".format(self.storage_path, self.requested)
