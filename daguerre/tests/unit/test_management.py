from django.core.files.storage import default_storage
import mock

from daguerre.management.commands._daguerre_clean import Command as Clean
from daguerre.models import AdjustedImage, Area
from daguerre.tests.base import BaseTestCase


class CleanTestCase(BaseTestCase):
    def test_old_adjustments(self):
        """
        _old_adjustments should return AdjustedImages whose storage_path
        no longer exists.

        """
        nonexistant = 'daguerre/test/nonexistant.png'
        if default_storage.exists(nonexistant):
            default_storage.delete(nonexistant)

        adjusted = self.create_image('100x100.png')
        adjusted1 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=nonexistant,
                                                 adjusted=adjusted)
        adjusted2 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=adjusted,
                                                 adjusted=adjusted)
        clean = Clean()
        self.assertEqual(list(clean._old_adjustments()), [adjusted1])
        default_storage.delete(adjusted)

    def test_old_areas(self):
        """
        _old_areas should return Areas whose storage_path no longer exists.

        """
        nonexistant = 'daguerre/test/nonexistant.png'
        if default_storage.exists(nonexistant):
            default_storage.delete(nonexistant)

        storage_path = self.create_image('100x100.png')
        kwargs = {
            'x1': 0,
            'x2': 10,
            'y1': 0,
            'y2': 10
        }
        area1 = Area.objects.create(storage_path=nonexistant,
                                    **kwargs)
        area2 = Area.objects.create(storage_path=storage_path,
                                    **kwargs)
        clean = Clean()
        self.assertEqual(list(clean._old_areas()), [area1])
        default_storage.delete(storage_path)

    def test_missing_adjustments(self):
        """
        _missing_adjustments should return AdjustedImages whose adjusted
        no longer exists.

        """
        nonexistant = 'daguerre/test/nonexistant.png'
        if default_storage.exists(nonexistant):
            default_storage.delete(nonexistant)

        storage_path = self.create_image('100x100.png')
        adjusted1 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=storage_path,
                                                 adjusted=nonexistant)
        adjusted2 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=storage_path,
                                                 adjusted=storage_path)
        clean = Clean()
        self.assertEqual(list(clean._missing_adjustments()), [adjusted1])
        default_storage.delete(storage_path)

    def test_duplicate_adjustments(self):
        path1 = self.create_image('100x100.png')
        path2 = self.create_image('100x100.png')
        adjusted1 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=path1,
                                                 adjusted=path1)
        adjusted2 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=path1,
                                                 adjusted=path1)
        adjusted3 = AdjustedImage.objects.create(requested='fit|50|50',
                                                 storage_path=path2,
                                                 adjusted=path1)
        clean = Clean()
        duplicates = clean._duplicate_adjustments()
        self.assertNotIn(adjusted3, duplicates)
        self.assertTrue(list(duplicates) == [adjusted1] or
                        list(duplicates) == [adjusted2])

    def test_orphaned_files(self):
        clean = Clean()
        walk_ret = (
            ('daguerre', ['test'], []),
            ('daguerre/test', [], ['fake1.png', 'fake2.png', 'fake3.png'])
        )
        AdjustedImage.objects.create(requested='fit|50|50',
                                     storage_path='whatever.png',
                                     adjusted='daguerre/test/fake2.png')
        with mock.patch.object(clean, '_walk', return_value=walk_ret) as walk:
            self.assertEqual(clean._orphaned_files(),
                             ['daguerre/test/fake1.png',
                              'daguerre/test/fake3.png'])
            walk.assert_called_once_with('daguerre', topdown=False)
