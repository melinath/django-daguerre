from django.core.files.storage import default_storage
from django.test import TestCase
try:
	from PIL import Image as PILImage
except ImportError:
	import Image as PILImage

from daguerre.models import AdjustedImage, Area, Image
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator, get_test_file_path
from daguerre.utils.adjustments import Fit, Crop, Fill, AdjustmentHelper, BulkAdjustmentHelper


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
		super(AdjustmentHelperTestCase, self).setUp()

	def test_adjust_crop__50x100(self):
		expected = PILImage.open(get_test_file_path('50x100_crop.png'))
		with self.assertNumQueries(4):
			adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

	def test_adjust_crop__100x50(self):
		expected = PILImage.open(get_test_file_path('100x50_crop.png'))
		with self.assertNumQueries(4):
			adjusted = AdjustmentHelper(self.base_image, width=100, height=50, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

	def test_adjust_crop__50x50_area(self):
		Area.objects.create(image=self.base_image, x1=21, x2=70, y1=46, y2=95)
		expected = PILImage.open(get_test_file_path('50x50_crop_area.png'))
		with self.assertNumQueries(4):
			adjusted = AdjustmentHelper(self.base_image, width=50, height=50, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), expected)

	def test_readjust(self):
		"""Adjusting a previously-adjusted image should return the previous adjustment."""
		new_im = PILImage.open(get_test_file_path('50x100_crop.png'))
		with self.assertNumQueries(4):
			adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertImageEqual(PILImage.open(adjusted.adjusted.path), new_im)

		with self.assertNumQueries(1):
			new_adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertEqual(adjusted, new_adjusted)

	def test_readjust_multiple(self):
		"""
		If there are multiple adjusted versions of the image with the same
		parameters, one of them should be returned rather than erroring out.

		"""
		with self.assertNumQueries(4):
			adjusted1 = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		adjusted2 = AdjustedImage.objects.get(pk=adjusted1.pk)
		adjusted2.pk = None
		adjusted2.save()
		self.assertNotEqual(adjusted1.pk, adjusted2.pk)

		with self.assertNumQueries(1):
			new_adjusted = AdjustmentHelper(self.base_image, width=50, height=100, adjustment='crop').adjust()
		self.assertTrue(new_adjusted == adjusted1 or new_adjusted == adjusted2)

	def test_adjust__nonexistant(self):
		"""
		Adjusting an Image for a path that (no longer) exists should raise an IOError.

		"""
		img = Image.objects.create(image='nonexistant.png', height=200, width=200)
		helper = AdjustmentHelper(img)
		# We still do get one query because the first try is always for
		# an AdjustedImage, whether or not the original Image path exists.
		with self.assertNumQueries(1):
			self.assertRaises(IOError, helper.adjust)


class BulkTestObject(object):
	def __init__(self, storage_path):
		self.storage_path = storage_path


class BulkAdjustmentHelperTestCase(DaguerreTestCaseMixin, TestCase):
	def test_info_dicts__non_bulk(self):
		image_creator = ImageCreator()
		images = [
			image_creator.create('100x100.png'),
			image_creator.create('100x100.png'),
			image_creator.create('100x50_crop.png'),
			image_creator.create('50x100_crop.png'),
		]

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}
		with self.assertNumQueries(4):
			for image in images:
				AdjustmentHelper(image, **kwargs).info_dict()

	def test_info_dicts__unprepped(self):
		image_creator = ImageCreator()
		images = [
			image_creator.create('100x100.png'),
			image_creator.create('100x100.png'),
			image_creator.create('100x50_crop.png'),
			image_creator.create('50x100_crop.png'),
		]
		iterable = [BulkTestObject(image.image.name) for image in images]
		# Explicitly unprep.
		Image.objects.all().delete()

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		helper = BulkAdjustmentHelper(iterable, 'storage_path', **kwargs)
		with self.assertNumQueries(3):
			helper.info_dicts()

		for image in Image.objects.all():
			self.assertTrue(default_storage.exists(image.image.name))

	def test_info_dicts__semiprepped(self):
		image_creator = ImageCreator()
		images = [
			image_creator.create('100x100.png'),
			image_creator.create('100x100.png'),
			image_creator.create('100x50_crop.png'),
			image_creator.create('50x100_crop.png'),
		]
		iterable = [BulkTestObject(image.image.name) for image in images]

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		helper = BulkAdjustmentHelper(iterable, 'storage_path', **kwargs)
		with self.assertNumQueries(2):
			helper.info_dicts()

	def test_info_dicts__prepped(self):
		image_creator = ImageCreator()
		images = [
			image_creator.create('100x100.png'),
			image_creator.create('100x100.png'),
			image_creator.create('100x50_crop.png'),
			image_creator.create('50x100_crop.png'),
		]
		iterable = [BulkTestObject(image.image.name) for image in images]

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		for image in images:
			AdjustmentHelper(image, **kwargs).adjust()

		helper = BulkAdjustmentHelper(iterable, 'storage_path', **kwargs)
		with self.assertNumQueries(1):
			helper.info_dicts()
