from django.test import TestCase
from django.core.files.storage import default_storage
try:
    from PIL import Image
except ImportError:
    import Image

from daguerre.tests.base import BaseTestCase
from daguerre.utils import (
    make_hash, save_image, get_exif_orientation,
    get_image_dimensions, apply_exif_orientation,
    exif_aware_size, DEFAULT_FORMAT, KEEP_FORMATS
)


class MakeHashTestCase(TestCase):
    def test_unicode(self):
        """
        Make sure that sha1 isn't choking on unicode characters.

        """
        hash_arg = u'banni\xe8re'
        make_hash(hash_arg)


class SaveImageTestCase(BaseTestCase):
    def test_keeper(self):
        """
        If the format is in KEEP_FORMATS, it should be preserved.

        """
        image = Image.open(self._data_path('100x100.png'))
        self.assertIn(image.format, KEEP_FORMATS)

        storage_path = save_image(image, 'daguerre/test/keeper.png',
                                  format=image.format)
        with default_storage.open(storage_path, 'rb') as f:
            new_image = Image.open(f)

        self.assertEqual(new_image.format, image.format)

    def test_non_keeper(self):
        """
        If the format is a weird one, such as a .psd, then the image should
        be saved as the default format rather than the original.

        """
        image = Image.open(self._data_path('100x50.psd'))
        self.assertNotIn(image.format, KEEP_FORMATS)

        storage_path = save_image(image, 'daguerre/test/nonkeeper.png',
                                  format=image.format)
        with default_storage.open(storage_path, 'rb') as f:
            new_image = Image.open(f)

        self.assertEqual(new_image.format, DEFAULT_FORMAT)


class GetExifOrientationTestCase(BaseTestCase):
    def test_exif(self):
        image = Image.open(self._data_path('20x7_exif_rotated.jpg'))
        orientation = get_exif_orientation(image)
        self.assertEqual(orientation, 6)

    def test_non_exif(self):
        "get_exif_orientation should return None if there is no Exif data."
        image = Image.open(self._data_path('20x7_no_exif.png'))
        orientation = get_exif_orientation(image)
        self.assertIsNone(orientation)


class ApplyExifOrientationTestCase(BaseTestCase):
    ORIGINAL_ORIENTATION = (20, 7)
    ROTATED_ORIENTATION = (7, 20)

    def test_exif_rotated(self):
        image = Image.open(self._data_path('20x7_exif_rotated.jpg'))
        image = apply_exif_orientation(image)
        self.assertEqual(image.size, self.ROTATED_ORIENTATION)

    def test_exif_not_rotated(self):
        "If rotation tag is 0, no rotation should be applied."
        image = Image.open(self._data_path('20x7_exif_not_rotated.jpg'))
        image = apply_exif_orientation(image)
        self.assertEqual(image.size, self.ORIGINAL_ORIENTATION)

    def test_non_exif(self):
        "If no exif data is present the original image should be left intact."
        original_image = Image.open(self._data_path('20x7_no_exif.png'))
        image = apply_exif_orientation(original_image)
        self.assertImageEqual(image, original_image)


class ExifAwareSizeTestCase(BaseTestCase):
    ORIGINAL_ORIENTATION = (20, 7)
    ROTATED_ORIENTATION = (7, 20)

    def test_exif_rotated(self):
        image = Image.open(self._data_path('20x7_exif_rotated.jpg'))
        self.assertEqual(exif_aware_size(image), self.ROTATED_ORIENTATION)

    def test_exif_not_rotated(self):
        image = Image.open(self._data_path('20x7_exif_not_rotated.jpg'))
        self.assertEqual(exif_aware_size(image), self.ORIGINAL_ORIENTATION)

    def test_non_exif(self):
        image = Image.open(self._data_path('20x7_no_exif.png'))
        self.assertEqual(exif_aware_size(image), self.ORIGINAL_ORIENTATION)


class GetImageDimensionsTestCase(BaseTestCase):
    ORIGINAL_ORIENTATION = (20, 7)
    ROTATED_ORIENTATION = (7, 20)

    def test_exif_rotated(self):
        dim = get_image_dimensions(self._data_path('20x7_exif_rotated.jpg'))
        self.assertEqual(dim, self.ROTATED_ORIENTATION)

    def test_exif_not_rotated(self):
        dim = get_image_dimensions(self._data_path('20x7_exif_not_rotated.jpg'))
        self.assertEqual(dim, self.ORIGINAL_ORIENTATION)

    def test_non_exif(self):
        dim = get_image_dimensions(self._data_path('20x7_no_exif.png'))
        self.assertEqual(dim, self.ORIGINAL_ORIENTATION)
