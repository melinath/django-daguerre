import os

from django.core.files.images import ImageFile
try:
	from PIL import ImageChops, Image as PILImage
except ImportError:
	import Image as PILImage
	import ImageChops

import daguerre
from daguerre.models import Image


def get_test_file_path(test_path):
		"""Given a path relative to daguerre/tests/data/, returns an absolute path."""
		return os.path.abspath(os.path.join(os.path.dirname(daguerre.__file__), 'tests', 'data', test_path))


def get_test_file(test_path):
	"""Given a path relative to daguerre/tests/data/, returns an open file."""
	return open(get_test_file_path(test_path))


class DaguerreTestCaseMixin(object):
	def assertImageEqual(self, im1, im2):
		# Image comparisons according to http://effbot.org/zone/pil-comparing-images.htm
		self.assertTrue(ImageChops.difference(im1, im2).getbbox() is None)


class ImageCreator(object):
	def create(self, test_path):
		pil_image = PILImage.open(get_test_file_path(test_path))
		image = Image()
		image.image = ImageFile(open(pil_image.filename))
		image.save()
		return image
