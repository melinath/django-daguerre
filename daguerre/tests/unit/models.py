import Image

from django.test import TestCase

from daguerre.models import AdjustedImage, Area
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator


class AdjustedImageTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()
		im = Image.open(self.get_test_file_path('100x100.png'))
		self.base_image = self.image_creator.create(im)

	def test_adjust_crop(self):
		expected = Image.open(self.get_test_file_path('50x100_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

		expected = Image.open(self.get_test_file_path('100x50_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=100, height=50, adjustment='crop')
		self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

		Area.objects.create(image=self.base_image, x1=21, x2=70, y1=46, y2=95)
		expected = Image.open(self.get_test_file_path('50x50_crop_area.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=50, adjustment='crop')
		self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

	def test_readjust(self):
		"""Adjusting a previously-adjusted image should return the previous adjustment."""
		new_im = Image.open(self.get_test_file_path('50x100_crop.png'))
		adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertImageEqual(Image.open(adjusted.adjusted.path), new_im)

		new_adjusted = AdjustedImage.objects.adjust(self.base_image, width=50, height=100, adjustment='crop')
		self.assertEqual(adjusted, new_adjusted)
