from django.core.files.storage import default_storage
from django.test import TestCase
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.models import AdjustedImage, Area, Image
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator, get_test_file_path


class AdjustedImageTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()
		self.base_image = self.image_creator.create('100x100.png')

	def test_adjust_crop(self):
		expected = PILImage.open(get_test_file_path('50x100_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

		expected = PILImage.open(get_test_file_path('100x50_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=100, height=50, adjustment='crop')
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

		Area.objects.create(image=self.base_image, x1=21, x2=70, y1=46, y2=95)
		expected = PILImage.open(get_test_file_path('50x50_crop_area.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=50, adjustment='crop')
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

	def test_readjust(self):
		"""Adjusting a previously-adjusted image should return the previous adjustment."""
		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), new_im)

		new_adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertEqual(adjusted, new_adjusted)

	def test_readjust_multiple(self):
		"""
		If there are multiple adjusted versions of the image with the same
		parameters, one of them should be returned rather than erroring out.

		"""
		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		adjusted1 = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		adjusted2 = AdjustedImage.objects.get(pk=adjusted1.pk)
		adjusted2.pk = None
		adjusted2.save()
		self.assertNotEqual(adjusted1.pk, adjusted2.pk)

		new_adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertTrue(new_adjusted == adjusted1 or new_adjusted == adjusted2)

	def test_adjust__nonexistant(self):
		"""
		Adjusting an Image for a path that (no longer) exists should raise a DoesNotExist.

		"""
		img = Image.objects.create(image='nonexistant.png', height=200, width=200)
		self.assertRaises(AdjustedImage.DoesNotExist, AdjustedImage.objects.adjust, img)


class ImageTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()

	def test_for_storage_path(self):
		image = self.image_creator.create('100x100.png')
		storage_path = image.image.name
		self.assertEqual(Image.objects.for_storage_path(storage_path), image)

	def test_for_storage_path__exact(self):
		"""
		The created Image for a given path should store that exact path rather
		than creating a copy of the file elsewhere.

		"""
		storage_path = 'exact_image_path.png'
		img = PILImage.open(get_test_file_path('100x100.png'))
		fp = default_storage.open(storage_path, 'w')
		img.save(fp, 'png')
		fp.close()

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
		image1 = self.image_creator.create('100x100.png')
		image2 = Image.objects.get(pk=image1.pk)
		image2.pk = None
		image2.save()
		self.assertNotEqual(image1.pk, image2.pk)

		storage_path = image1.image.name
		new_image = Image.objects.for_storage_path(storage_path)
		self.assertTrue(new_image == image1 or new_image == image2)
