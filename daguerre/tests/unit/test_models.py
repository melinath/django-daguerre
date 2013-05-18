from daguerre.models import AdjustedImage
from daguerre.tests.base import BaseTestCase


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
