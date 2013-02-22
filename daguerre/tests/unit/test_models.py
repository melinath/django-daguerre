import os

from django.core.files.storage import default_storage
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.models import Image, DEFAULT_FORMAT, KEEP_FORMATS
from daguerre.tests.base import BaseTestCase


class ImageTestCase(BaseTestCase):
	def test_for_storage_path(self):
		image = self.create_image('100x100.png')
		storage_path = image.image.name
		self.assertEqual(Image.objects.for_storage_path(storage_path), image)

	def test_for_storage_path__exact(self):
		"""
		The created Image for a given path should store that exact path rather
		than creating a copy of the file elsewhere, if the format is a keeper.

		"""
		storage_path = 'exact_image_path.png'
		with self._data_file('100x100.png') as f:
			with default_storage.open(storage_path, 'w') as target:
				target.write(f.read())

		with default_storage.open(storage_path, 'r') as f:
			im = PILImage.open(f)
		self.assertIn(im.format, KEEP_FORMATS)

		image = Image.objects.for_storage_path(storage_path)
		self.assertEqual(image.image.name, storage_path)

	def test_for_storage_path__nonexistant(self):
		"""Nonexistant paths should raise Image.DoesNotExist."""
		self.assertRaises(Image.DoesNotExist, Image.objects.for_storage_path, 'nonexistant.png')

	def test_for_storage_path__not_image(self):
		"""Paths that aren't images should raise Image.DoesNotExist."""
		fp = default_storage.open('totally-an-image.jpg', 'w')
		fp.write('hi')
		fp.close()
		self.assertRaises(Image.DoesNotExist, Image.objects.for_storage_path, 'totally-an-image.jpg')

	def test_for_storage_path__multiple(self):
		"""
		If multiple Images exist for a certain storage path, one of them should
		be returned rather than erroring out.

		"""
		image1 = self.create_image('100x100.png')
		image2 = Image.objects.get(pk=image1.pk)
		image2.pk = None
		image2.save()
		self.assertNotEqual(image1.pk, image2.pk)

		storage_path = image1.image.name
		new_image = Image.objects.for_storage_path(storage_path)
		self.assertTrue(new_image == image1 or new_image == image2)

	def test_for_storage_path__non_keeper(self):
		"""
		If the format is a weird one, such as a .psd, then the image should
		be re-saved as the default format.

		"""
		storage_path = 'non_keeper.psd'
		with self._data_file('100x50.psd') as f:
			with default_storage.open(storage_path, 'w') as target:
				target.write(f.read())

		with default_storage.open(storage_path, 'r') as f:
			im = PILImage.open(f)
		self.assertNotIn(im.format, KEEP_FORMATS)
		self.assertNotEqual(im.format, DEFAULT_FORMAT)

		image = Image.objects.for_storage_path(storage_path)
		image.image.open()
		im = PILImage.open(image.image)
		self.assertEqual(im.format, DEFAULT_FORMAT)
		self.assertNotEqual(image.image.name, storage_path)
		self.assertEqual(os.path.splitext(image.image.name)[1][1:], DEFAULT_FORMAT.lower())

		image2 = Image.objects.for_storage_path(storage_path)
		self.assertEqual(image, image2)
