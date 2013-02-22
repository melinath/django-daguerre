import os

from django.core.files.images import ImageFile
from django.test import TestCase
try:
	from PIL import ImageChops, Image as PILImage
except ImportError:
	import Image as PILImage
	import ImageChops

import daguerre
from daguerre.models import Image


TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(daguerre.__file__), 'tests', 'data'))


class BaseTestCase(TestCase):
	@classmethod
	def _data_path(cls, test_path):
		"""Given a path relative to daguerre/tests/data/, returns an absolute path."""
		return os.path.join(TEST_DATA_DIR, test_path)

	@classmethod
	def _data_file(cls, test_path, mode='r'):
		"""Given a path relative to daguerre/tests/data/, returns an open file."""
		return open(cls._data_path(test_path), mode)

	def assertImageEqual(self, im1, im2):
		# Image comparisons according to http://effbot.org/zone/pil-comparing-images.htm
		self.assertTrue(ImageChops.difference(im1, im2).getbbox() is None)

	def create_image(self, test_path):
		pil_image = PILImage.open(self._data_path(test_path))
		image = Image()
		with open(pil_image.filename, 'r') as f:
			image.image = ImageFile(f)
			image.save()
		image.storage_path = image.image.name
		image.save()
		return image
