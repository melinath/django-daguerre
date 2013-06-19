from django.test import TestCase
from django.core.files.storage import default_storage
try:
    from PIL import Image
except ImportError:
    import Image

from daguerre.tests.base import BaseTestCase
from daguerre.utils import make_hash, save_image, DEFAULT_FORMAT, KEEP_FORMATS


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
