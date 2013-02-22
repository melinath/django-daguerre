import os

from django.test import TestCase
try:
	from PIL import ImageChops, Image
except ImportError:
	import Image
	import ImageChops

import daguerre
from daguerre.utils import save_image


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
		image = Image.open(self._data_path(test_path))
		return save_image(image, 'daguerre/test/{0}'.format(test_path))
