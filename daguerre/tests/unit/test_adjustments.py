from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
try:
    from PIL import Image
except ImportError:
    import Image

from daguerre.adjustments import Fit, Crop, Fill, NamedCrop
from daguerre.helpers import AdjustmentHelper
from daguerre.models import AdjustedImage, Area
from daguerre.tests.base import BaseTestCase


class FitTestCase(BaseTestCase):
    def test_calculate__both(self):
        fit = Fit(width=50, height=50)
        self.assertEqual(fit.calculate((100, 100)), (50, 50))

    def test_calculate__width(self):
        fit = Fit(width=50)
        self.assertEqual(fit.calculate((100, 100)), (50, 50))

    def test_calculate__height(self):
        fit = Fit(height=50)
        self.assertEqual(fit.calculate((100, 100)), (50, 50))

    def test_calculate__smallest(self):
        fit = Fit(width=60, height=50)
        self.assertEqual(fit.calculate((100, 100)), (50, 50))

    def test_adjust__both(self):
        im = Image.open(self._data_path('100x100.png'))
        fit = Fit(width=50, height=50)
        adjusted = fit.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__width(self):
        im = Image.open(self._data_path('100x100.png'))
        fit = Fit(width=50)
        adjusted = fit.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__height(self):
        im = Image.open(self._data_path('100x100.png'))
        fit = Fit(height=50)
        adjusted = fit.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__smallest(self):
        im = Image.open(self._data_path('100x100.png'))
        fit = Fit(width=60, height=50)
        adjusted = fit.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)


class CropTestCase(BaseTestCase):
    def test_calculate__both(self):
        crop = Crop(width=50, height=50)
        self.assertEqual(crop.calculate((100, 100)), (50, 50))

    def test_calculate__width(self):
        crop = Crop(width=50)
        self.assertEqual(crop.calculate((100, 100)), (50, 100))

    def test_calculate__height(self):
        crop = Crop(height=50)
        self.assertEqual(crop.calculate((100, 100)), (100, 50))

    def test_adjust__both(self):
        im = Image.open(self._data_path('100x100.png'))
        crop = Crop(width=50, height=50)
        adjusted = crop.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_crop.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__width(self):
        im = Image.open(self._data_path('100x100.png'))
        crop = Crop(width=50)
        adjusted = crop.adjust(im)
        self.assertEqual(adjusted.size, (50, 100))
        expected = Image.open(self._data_path('50x100_crop.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__height(self):
        im = Image.open(self._data_path('100x100.png'))
        crop = Crop(height=50)
        adjusted = crop.adjust(im)
        self.assertEqual(adjusted.size, (100, 50))
        expected = Image.open(self._data_path('100x50_crop.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__area(self):
        im = Image.open(self._data_path('100x100.png'))
        crop = Crop(width=50, height=50)
        areas = [Area(x1=21, y1=46, x2=70, y2=95)]
        adjusted = crop.adjust(im, areas=areas)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_crop_area.png'))
        self.assertImageEqual(adjusted, expected)


class FillTestCase(BaseTestCase):
    def test_calculate__both(self):
        fill = Fill(width=50, height=50)
        self.assertEqual(fill.calculate((100, 100)), (50, 50))

    def test_calculate__unequal(self):
        fill = Fill(width=50, height=40)
        self.assertEqual(fill.calculate((100, 100)), (50, 40))

    def test_calculate__width(self):
        fill = Fill(width=50)
        self.assertEqual(fill.calculate((100, 100)), (50, 50))

    def test_calculate__height(self):
        fill = Fill(height=50)
        self.assertEqual(fill.calculate((100, 100)), (50, 50))

    def test_calculate__max_height(self):
        fill = Fill(width=50, max_height=200)
        self.assertEqual(fill.calculate((100, 100)), (50, 50))

    def test_calculate__max_width(self):
        fill = Fill(height=50, max_width=200)
        self.assertEqual(fill.calculate((100, 100)), (50, 50))

    def test_calculate__max_height__smaller(self):
        fill = Fill(width=100, max_height=50)
        self.assertEqual(fill.calculate((100, 100)), (100, 50))

    def test_calculate__max_width__smaller(self):
        fill = Fill(height=100, max_width=50)
        self.assertEqual(fill.calculate((100, 100)), (50, 100))

    def test_adjust__both(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(width=50, height=50)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__width(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(width=50)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__height(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(height=50)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__max_height(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(width=50, max_height=200)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__max_width(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(height=50, max_width=200)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 50))
        expected = Image.open(self._data_path('50x50_fit.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__unequal(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(width=50, height=40)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 40))
        expected = Image.open(self._data_path('50x40_fill.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__max_height__smaller(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(width=100, max_height=50)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (100, 50))
        expected = Image.open(self._data_path('100x50_crop.png'))
        self.assertImageEqual(adjusted, expected)

    def test_adjust__max_width__smaller(self):
        im = Image.open(self._data_path('100x100.png'))
        fill = Fill(height=100, max_width=50)
        adjusted = fill.adjust(im)
        self.assertEqual(adjusted.size, (50, 100))
        expected = Image.open(self._data_path('50x100_crop.png'))
        self.assertImageEqual(adjusted, expected)


class AdjustmentHelperTestCase(BaseTestCase):
    def setUp(self):
        self.base_image = self.create_image('100x100.png')
        super(AdjustmentHelperTestCase, self).setUp()

    def test_adjust_crop__50x100(self):
        expected = Image.open(self._data_path('50x100_crop.png'))
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [Crop(width=50, height=100)]
                             ).adjust()
        adjusted = AdjustedImage.objects.get()
        self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)
        # Make sure that the path is properly formatted.
        self.assertTrue(adjusted.adjusted.path.endswith('.png'))

    def test_adjust_crop__100x50(self):
        expected = Image.open(self._data_path('100x50_crop.png'))
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [Crop(width=100, height=50)]
                             ).adjust()
        adjusted = AdjustedImage.objects.get()
        self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

    def test_adjust_crop__50x50_area(self):
        self.create_area(storage_path=self.base_image, x1=21, x2=70, y1=46,
                         y2=95)
        expected = Image.open(self._data_path('50x50_crop_area.png'))
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [Crop(width=50, height=50)]
                             ).adjust()
        adjusted = AdjustedImage.objects.get()
        self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

    def test_named_crop(self):
        self.create_area(storage_path=self.base_image, x1=21, x2=70, y1=46,
                         y2=95, name='area')
        expected = Image.open(self._data_path('25x25_fit_named_crop.png'))
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [NamedCrop(name='area'),
                              Fit(width=25, height=25)]
                             ).adjust()
        adjusted = AdjustedImage.objects.get()
        self.assertImageEqual(Image.open(adjusted.adjusted.path), expected)

    def test_readjust(self):
        """
        Adjusting a previously-adjusted image should return the previous
        adjustment.

        """
        new_im = Image.open(self._data_path('50x100_crop.png'))
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [Crop(width=50, height=100)]
                             ).adjust()
        adjusted = AdjustedImage.objects.get()
        self.assertImageEqual(Image.open(adjusted.adjusted.path), new_im)

        with self.assertNumQueries(1):
            AdjustmentHelper([self.base_image],
                             [Crop(width=50, height=100)]
                             ).adjust()
        self.assertEqual(AdjustedImage.objects.count(), 1)

    def test_readjust_multiple(self):
        """
        If there are multiple adjusted versions of the image with the same
        parameters, one of them should be returned rather than erroring out.

        """
        with self.assertNumQueries(4):
            AdjustmentHelper([self.base_image],
                             [Crop(width=50, height=100)]
                             ).adjust()
        adjusted1 = AdjustedImage.objects.get()
        adjusted2 = AdjustedImage.objects.get()
        adjusted2.pk = None
        adjusted2.save()
        self.assertNotEqual(adjusted1.pk, adjusted2.pk)

        helper = AdjustmentHelper([self.base_image],
                                  [Crop(width=50, height=100)])
        with self.assertNumQueries(1):
            helper.adjust()
        url = helper.adjusted.values()[0]['url']
        self.assertEqual(url, adjusted1.adjusted.url)
        self.assertEqual(url, adjusted2.adjusted.url)

    def test_adjust__nonexistant(self):
        """
        Adjusting a path that doesn't exist should raise an IOError.

        """
        storage_path = 'nonexistant.png'
        self.assertFalse(default_storage.exists(storage_path))
        helper = AdjustmentHelper([storage_path], [Fit(width=50, height=50)])
        # We still do get one query because the first try is always for
        # an AdjustedImage, whether or not the original file exists.
        # This is for historic reasons and doesn't necessarily need to
        # continue to be the case.
        with self.assertNumQueries(1):
            helper.adjust()
        self.assertEqual(helper.adjusted, {helper.iterable[0]: {}})
        self.assertEqual(helper.remaining, {})

    def test_adjust__broken(self):
        broken_file = self._data_file('broken.png')
        storage_path = default_storage.save('daguerre/test/broken.png',
                                            ContentFile(broken_file.read()))
        broken_file = default_storage.open(storage_path)
        image = Image.open(broken_file)
        self.assertRaises(IndexError, image.verify)

        helper = AdjustmentHelper([storage_path],
                                  [Fill(width=50, height=50)])
        with self.assertNumQueries(1):
            helper.adjust()
        self.assertEqual(helper.adjusted, {helper.iterable[0]: {}})
        self.assertEqual(helper.remaining, {})


class BulkTestObject(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path


class BulkAdjustmentHelperTestCase(BaseTestCase):
    def test_info_dicts__non_bulk(self):
        images = [
            self.create_image('100x100.png'),
            self.create_image('100x100.png'),
            self.create_image('100x50_crop.png'),
            self.create_image('50x100_crop.png'),
        ]

        adj = Crop(width=50, height=50)
        with self.assertNumQueries(4):
            for image in images:
                AdjustmentHelper([image], [adj]).info_dicts()

    def test_info_dicts__unprepped(self):
        images = [
            self.create_image('100x100.png'),
            self.create_image('100x100.png'),
            self.create_image('100x50_crop.png'),
            self.create_image('50x100_crop.png'),
        ]
        iterable = [BulkTestObject(image) for image in images]

        adj = Crop(width=50, height=50)

        helper = AdjustmentHelper(iterable, [adj], 'storage_path')
        with self.assertNumQueries(1):
            helper.info_dicts()

    def test_info_dicts__semiprepped(self):
        images = [
            self.create_image('100x100.png'),
            self.create_image('100x100.png'),
            self.create_image('100x50_crop.png'),
            self.create_image('50x100_crop.png'),
        ]
        iterable = [BulkTestObject(image) for image in images]

        adj = Crop(width=50, height=50)

        helper = AdjustmentHelper(iterable, [adj], 'storage_path')
        with self.assertNumQueries(1):
            helper.info_dicts()

    def test_info_dicts__prepped(self):
        images = [
            self.create_image('100x100.png'),
            self.create_image('100x100.png'),
            self.create_image('100x50_crop.png'),
            self.create_image('50x100_crop.png'),
        ]
        iterable = [BulkTestObject(image) for image in images]

        adj = Crop(width=50, height=50)

        helper = AdjustmentHelper(iterable, [adj], 'storage_path')
        helper.adjust()

        helper = AdjustmentHelper(iterable, [adj], 'storage_path')
        with self.assertNumQueries(1):
            helper.info_dicts()

    def test_lookup(self):
        storage_path = 'path/to/somewhe.re'
        iterable = [
            BulkTestObject({'bar': storage_path})
        ]
        helper = AdjustmentHelper(iterable,
                                  [Fit(width=50, height=50)],
                                  "storage_path.bar")
        self.assertEqual(helper.adjusted, {})
        self.assertEqual(helper.remaining, {storage_path: [iterable[0]]})

    def test_lookup__invalid(self):
        storage_path = 'path/to/somewhe.re'
        iterable = [
            BulkTestObject({'_bar': storage_path})
        ]
        helper = AdjustmentHelper(iterable,
                                  [Fit(width=50, height=50)],
                                  "storage_path._bar")
        self.assertEqual(helper.adjusted, {iterable[0]: {}})
        self.assertEqual(helper.remaining, {})
