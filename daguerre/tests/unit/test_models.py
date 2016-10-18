import warnings

from daguerre.models import AdjustedImage, upload_to
from daguerre.tests.base import BaseTestCase

from django.test.utils import override_settings


class AreaTestCase(BaseTestCase):
    def test_delete_adjusted_images__save(self):
        """
        Saving an adjusted image should delete "related" adjusted images
        that use areas.

        """
        storage_path = self.create_image('100x100.png')
        kwargs = {
            'storage_path': storage_path,
            'adjusted': storage_path,
        }
        area = self.create_area(storage_path=storage_path)
        adjusted1 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 **kwargs)
        adjusted2 = AdjustedImage.objects.create(requested='crop|50|50',
                                                 **kwargs)

        area.save()

        self.assertRaises(AdjustedImage.DoesNotExist,
                          AdjustedImage.objects.get,
                          pk=adjusted2.pk)
        AdjustedImage.objects.get(pk=adjusted1.pk)

    def test_delete_adjusted_images__delete(self):
        """
        Deleting an adjusted image should delete "related" adjusted images that
        use areas.

        """
        storage_path = self.create_image('100x100.png')
        kwargs = {
            'storage_path': storage_path,
            'adjusted': storage_path,
        }
        area = self.create_area(storage_path=storage_path)
        adjusted1 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 **kwargs)
        adjusted2 = AdjustedImage.objects.create(requested='crop|50|50',
                                                 **kwargs)

        area.delete()

        self.assertRaises(AdjustedImage.DoesNotExist,
                          AdjustedImage.objects.get,
                          pk=adjusted2.pk)
        AdjustedImage.objects.get(pk=adjusted1.pk)


class AdjustedImageUploadToTestCase(BaseTestCase):

    def setUp(self):
        self.instance = None
        self.filename = '7014c0bdbedea0e4f4bf.jpeg'

    def test_upload_to__default_upload_dir(self):
        with warnings.catch_warnings(record=True) as w:
            hash_path = upload_to(
                instance=self.instance, filename=self.filename)
            self.assertTrue(hash_path.startswith('dg/'))
            self.assertTrue(hash_path.endswith('/{}'.format(self.filename)))
            self.assertEqual(len(hash_path.split('/')), 4)
            self.assertTrue(len(hash_path) < 45)
            self.assertEqual(w, [])

    @override_settings(DAGUERRE_ADJUSTED_IMAGE_PATH='img')
    def test_upload_to__custom_upload_dir(self):
        with warnings.catch_warnings(record=True) as w:
            hash_path = upload_to(
                instance=self.instance, filename=self.filename)
            self.assertTrue(hash_path.startswith('img/'))
            self.assertTrue(hash_path.endswith('/{}'.format(self.filename)))
            self.assertEqual(len(hash_path.split('/')), 4)
            self.assertTrue(len(hash_path) < 45)
            self.assertEqual(w, [])

    @override_settings(DAGUERRE_ADJUSTED_IMAGE_PATH='0123456789123')
    def test_upload_to__custom_upload_dir_small(self):
        with warnings.catch_warnings(record=True) as w:
            hash_path = upload_to(
                instance=self.instance, filename=self.filename)
            self.assertTrue(hash_path.startswith('0123456789123/'))
            self.assertTrue(hash_path.endswith('/{}'.format(self.filename)))
            self.assertEqual(len(hash_path.split('/')), 4)
            self.assertTrue(len(hash_path) == 45)
            self.assertEqual(w, [])

    @override_settings(DAGUERRE_ADJUSTED_IMAGE_PATH='01234567891234')
    def test_upload_to__custom_upload_dir_big(self):
        with warnings.catch_warnings(record=True) as w:
            hash_path = upload_to(
                instance=self.instance, filename=self.filename)
            self.assertTrue(hash_path.startswith('dg/'))
            self.assertTrue(hash_path.endswith('/{}'.format(self.filename)))
            self.assertEqual(len(hash_path.split('/')), 4)
            self.assertTrue(len(hash_path) < 45)

            # Test the warning message
            # https://docs.python.org/2/library/warnings.html#testing-warnings
            warning_message = ('The DAGUERRE_PATH value is more than 13 '
                               'characters long! Falling back to the default '
                               'value: "dg".')

            self.assertEqual(len(w), 1)
            user_warning = w[0]
            self.assertEqual(user_warning.category, UserWarning)
            self.assertEqual(user_warning.message.__str__(), warning_message)
