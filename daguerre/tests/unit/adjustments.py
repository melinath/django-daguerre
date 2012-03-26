from django.test import TestCase
try:
	from PIL import Image
except ImportError:
	import Image

from daguerre.models import Area
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator, get_test_file_path
from daguerre.utils.adjustments import Adjustment, Fit, Crop, Fill


class AdjustmentTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()
		TestCase.setUp(self)

	def test_from_image(self):
		image = self.image_creator.create('100x100.png')
		adjustment = Adjustment.from_image(image)
		self.assertTrue(adjustment._crop is None)
		self.assertTrue(adjustment._crop_area is None)
		self.assertEqual(adjustment._storage_path, image.image.name)
		self.assertEqual(adjustment._image, image)
		self.assertEqual(list(adjustment.areas), list(image.areas.all()))
		self.assertEqual(adjustment.format, 'PNG')
		self.assertEqual(adjustment.mimetype, 'image/png')
		self.assertTrue(adjustment.width is None)
		self.assertTrue(adjustment.height is None)
		self.assertTrue(adjustment.max_width is None)
		self.assertTrue(adjustment.max_height is None)


class FitTestCase(DaguerreTestCaseMixin, TestCase):
	def test_calculate(self):
		im = Image.open(get_test_file_path('100x100.png'))
		fit = Fit(im, width=50, height=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, width=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, height=50)
		self.assertEqual(fit.calculate(), (50, 50))
		fit = Fit(im, width=60, height=50)
		self.assertEqual(fit.calculate(), (50, 50))

	def test_adjust(self):
		im = Image.open(get_test_file_path('100x100.png'))
		new_im = Image.open(get_test_file_path('50x50_fit.png'))
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
		im = Image.open(get_test_file_path('100x100.png'))
		crop = Crop(im, width=50, height=50)
		self.assertEqual(crop.calculate(), (50, 50))
		crop = Crop(im, width=50)
		self.assertEqual(crop.calculate(), (50, 100))
		crop = Crop(im, height=50)
		self.assertEqual(crop.calculate(), (100, 50))

	def test_adjust(self):
		im = Image.open(get_test_file_path('100x100.png'))

		new_im = Image.open(get_test_file_path('50x50_crop.png'))
		crop = Crop(im, width=50, height=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = Image.open(get_test_file_path('50x100_crop.png'))
		crop = Crop(im, width=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = Image.open(get_test_file_path('100x50_crop.png'))
		crop = Crop(im, height=50)
		self.assertImageEqual(crop.adjust(), new_im)

		new_im = Image.open(get_test_file_path('50x50_crop_area.png'))
		crop = Crop(im, width=50, height=50, areas=[Area(x1=21, y1=46, x2=70, y2=95)])
		self.assertImageEqual(crop.adjust(), new_im)


class FillTestCase(DaguerreTestCaseMixin, TestCase):
	def test_calculate(self):
		im = Image.open(get_test_file_path('100x100.png'))
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
		im = Image.open(get_test_file_path('100x100.png'))

		new_im = Image.open(get_test_file_path('50x50_fit.png'))
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

		new_im = Image.open(get_test_file_path('50x40_fill.png'))
		fill = Fill(im, width=50, height=40)
		self.assertImageEqual(fill.adjust(), new_im)

		new_im = Image.open(get_test_file_path('100x50_crop.png'))
		fill = Fill(im, width=100, max_height=50)
		self.assertImageEqual(fill.adjust(), new_im)

		new_im = Image.open(get_test_file_path('50x100_crop.png'))
		fill = Fill(im, height=100, max_width=50)
		self.assertImageEqual(fill.adjust(), new_im)
