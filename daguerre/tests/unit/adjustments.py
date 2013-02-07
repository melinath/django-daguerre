from django.test import TestCase
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.models import AdjustedImage, Area, Image
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator, get_test_file_path
from daguerre.utils.adjustments import Fit, Crop, Fill, AdjustmentHelper


class FitTestCase(DaguerreTestCaseMixin, TestCase):
	def test_calculate(self):
		im = PILImage.open(get_test_file_path('100x100.png'))
		fit = Fit(im, width=50, height=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, width=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, height=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, width=60, height=50)
		self.assertEqual(fit.calculate(), (50, 50))

	def test_adjust(self):
		im = PILImage.open(get_test_file_path('100x100.png'))
		new_im = PILImage.open(get_test_file_path('50x50_fit.png'))
		fit = Fit(im, width=50, height=50)
		self.assertImageEqual(fit.adjust(), new_im)
		fit = Fit(im, width=50)
		self.assertImageEqual(fit.adjust(), new_im)
		fit = Fit(im, height=50)
		self.assertImageEqual(fit.adjust(), new_im)
		fit = Fit(im, width=60, height=50)
		self.assertImageEqual(fit.adjust(), new_im)


class CropTestCase(DaguerreTestCaseMixin, TestCase):
	def test_calculate(self):
		im = PILImage.open(get_test_file_path('100x100.png'))
		crop = Crop(im, width=50, height=50)
		self.assertEqual(crop.calculate(), (50, 50))
		crop = Crop(im, width=50)
		self.assertEqual(crop.calculate(), (50, 100))
		crop = Crop(im, height=50)
		self.assertEqual(crop.calculate(), (100, 50))

	def test_adjust(self):
		im = PILImage.open(get_test_file_path('100x100.png'))

		new_im = PILImage.open(get_test_file_path('50x50_crop.png'))
		crop = Crop(im, width=50, height=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		crop = Crop(im, width=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('100x50_crop.png'))
		crop = Crop(im, height=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('50x50_crop_area.png'))
		crop = Crop(im, width=50, height=50, areas=[Area(x1=21, y1=46, x2=70, y2=95)])
		self.assertImageEqual(crop.adjust(), new_im)


class FillTestCase(DaguerreTestCaseMixin, TestCase):
	def test_calculate(self):
		im = PILImage.open(get_test_file_path('100x100.png'))
		fill = Fill(im, width=50, height=50)
		self.assertEqual(fill.calculate(), (50, 50))
		fill = Fill(im, width=50, height=40)
		self.assertEqual(fill.calculate(), (50, 40))
		fill = Fill(im, width=50)
		self.assertEqual(fill.calculate(), (50, 50))
		fill = Fill(im, height=50)
		self.assertEqual(fill.calculate(), (50, 50))
		fill = Fill(im, width=50, max_height=200)
		self.assertEqual(fill.calculate(), (50, 50))
		fill = Fill(im, height=50, max_width=200)
		self.assertEqual(fill.calculate(), (50, 50))
		fill = Fill(im, width=100, max_height=50)
		self.assertEqual(fill.calculate(), (100, 50))
		fill = Fill(im, height=100, max_width=50)
		self.assertEqual(fill.calculate(), (50, 100))

	def test_adjust(self):
		im = PILImage.open(get_test_file_path('100x100.png'))

		new_im = PILImage.open(get_test_file_path('50x50_fit.png'))
		fill = Fill(im, width=50, height=50)
		self.assertImageEqual(fill.adjust(), new_im)
		fill = Fill(im, width=50)
		self.assertImageEqual(fill.adjust(), new_im)
		fill = Fill(im, height=50)
		self.assertImageEqual(fill.adjust(), new_im)
		fill = Fill(im, width=50, max_height=200)
		self.assertImageEqual(fill.adjust(), new_im)
		fill = Fill(im, height=50, max_width=200)
		self.assertImageEqual(fill.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('50x40_fill.png'))
		fill = Fill(im, width=50, height=40)
		self.assertImageEqual(fill.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('100x50_crop.png'))
		fill = Fill(im, width=100, max_height=50)
		self.assertImageEqual(fill.adjust(), new_im)

		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		fill = Fill(im, height=100, max_width=50)
		self.assertImageEqual(fill.adjust(), new_im)


class AdjustmentHelperTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()
		self.base_image = self.image_creator.create('100x100.png')

	def test_adjust_crop(self):
		expected = PILImage.open(get_test_file_path('50x100_crop.png'))
		adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

		expected = PILImage.open(get_test_file_path('100x50_crop.png'))
		adjusted = AdjustmentHelper(self.base_image, width=100, height=50, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

		Area.objects.create(image=self.base_image, x1=21, x2=70, y1=46, y2=95)
		expected = PILImage.open(get_test_file_path('50x50_crop_area.png'))
		adjusted = AdjustmentHelper(self.base_image, width=50, height=50, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

	def test_readjust(self):
		"""Adjusting a previously-adjusted image should return the previous adjustment."""
		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), new_im)

		new_adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertEqual(adjusted, new_adjusted)

	def test_readjust_multiple(self):
		"""
		If there are multiple adjusted versions of the image with the same
		parameters, one of them should be returned rather than erroring out.

		"""
		adjusted1 = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		adjusted2 = AdjustedImage.objects.get(pk=adjusted1.pk)
		adjusted2.pk = None
		adjusted2.save()
		self.assertNotEqual(adjusted1.pk, adjusted2.pk)

		new_adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertTrue(new_adjusted == adjusted1 or new_adjusted == adjusted2)

	def test_adjust__nonexistant(self):
		"""
		Adjusting an Image for a path that (no longer) exists should raise an IOError.

		"""
		img = Image.objects.create(image='nonexistant.png', height=200, width=200)
		helper = AdjustmentHelper(img)
		self.assertRaises(IOError, helper.adjust)
