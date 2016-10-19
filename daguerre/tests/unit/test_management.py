from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import CommandError
from django.test.utils import override_settings
import mock

from daguerre.adjustments import Fit
from daguerre.management.commands._daguerre_clean import Command as Clean
from daguerre.management.commands._daguerre_preadjust import (
    NO_ADJUSTMENTS,
    BAD_STRUCTURE,
    Command as Preadjust,
)
from daguerre.management.commands.daguerre import Command as Daguerre
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
        AdjustedImage.objects.create(requested='fit|50|50',
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
        Area.objects.create(storage_path=storage_path,
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
        AdjustedImage.objects.create(requested='fit|50|50',
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

    def test_orphaned_files__default_path(self):
        clean = Clean()
        walk_ret = (
            ('dg', ['test'], []),
            ('dg/test', [], ['fake1.png', 'fake2.png', 'fake3.png'])
        )
        AdjustedImage.objects.create(requested='fit|50|50',
                                     storage_path='whatever.png',
                                     adjusted='dg/test/fake2.png')
        with mock.patch.object(clean, '_walk', return_value=walk_ret) as walk:
            self.assertEqual(clean._orphaned_files(),
                             ['dg/test/fake1.png',
                              'dg/test/fake3.png'])
            walk.assert_called_once_with('dg', topdown=False)

    @override_settings(DAGUERRE_ADJUSTED_IMAGE_PATH='img')
    def test_orphaned_files__modified_path(self):
        clean = Clean()
        walk_ret = (
            ('img', ['test'], []),
            ('img/test', [], ['fake1.png', 'fake2.png', 'fake3.png'])
        )
        AdjustedImage.objects.create(requested='fit|50|50',
                                     storage_path='whatever.png',
                                     adjusted='img/test/fake2.png')
        with mock.patch.object(clean, '_walk', return_value=walk_ret) as walk:
            self.assertEqual(clean._orphaned_files(),
                             ['img/test/fake1.png',
                              'img/test/fake3.png'])
            walk.assert_called_once_with('img', topdown=False)


class PreadjustTestCase(BaseTestCase):
    @override_settings()
    def test_get_helpers__no_setting(self):
        try:
            del settings.DAGUERRE_PREADJUSTMENTS
        except AttributeError:
            pass
        preadjust = Preadjust()
        self.assertRaisesMessage(CommandError,
                                 NO_ADJUSTMENTS,
                                 preadjust._get_helpers)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        ('model', [Fit(width=50)], None),))
    def test_get_helpers__bad_string(self):
        preadjust = Preadjust()
        self.assertRaisesMessage(CommandError,
                                 BAD_STRUCTURE,
                                 preadjust._get_helpers)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        ('app.model', [Fit(width=50)], None),))
    def test_get_helpers__bad_model(self):
        preadjust = Preadjust()
        self.assertRaisesMessage(CommandError,
                                 BAD_STRUCTURE,
                                 preadjust._get_helpers)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(1, 2, 3))
    def test_get_helpers__not_tuples(self):
        preadjust = Preadjust()
        self.assertRaisesMessage(CommandError,
                                 BAD_STRUCTURE,
                                 preadjust._get_helpers)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        ('daguerre.adjustedimage', [], 'storage_path'),))
    def test_get_helpers__no_adjustments(self):
        preadjust = Preadjust()
        self.assertRaisesMessage(CommandError,
                                 BAD_STRUCTURE,
                                 preadjust._get_helpers)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        ('daguerre.adjustedimage', [Fit(width=50)], 'storage_path'),))
    def test_get_helpers__good_string(self):
        preadjust = Preadjust()
        helpers = preadjust._get_helpers()
        self.assertEqual(len(helpers), 1)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        (AdjustedImage, [Fit(width=50)], 'storage_path'),))
    def test_get_helpers__model(self):
        preadjust = Preadjust()
        helpers = preadjust._get_helpers()
        self.assertEqual(len(helpers), 1)

    def test_get_helpers__queryset(self):
        preadjust = Preadjust()
        qs = AdjustedImage.objects.all()
        dp = ((qs, [Fit(width=50)], 'storage_path'),)
        with override_settings(DAGUERRE_PREADJUSTMENTS=dp):
            helpers = preadjust._get_helpers()
        self.assertEqual(len(helpers), 1)
        self.assertTrue(qs._result_cache is None)

    def test_get_helpers__iterable(self):
        preadjust = Preadjust()
        storage_path = self.create_image('100x100.png')
        adjusted = AdjustedImage.objects.create(storage_path=storage_path,
                                                adjusted=storage_path)

        def _iter():
            yield adjusted

        dp = ((_iter(), [Fit(width=50)], 'storage_path'),)

        with override_settings(DAGUERRE_PREADJUSTMENTS=dp):
            helpers = preadjust._get_helpers()
        self.assertEqual(len(helpers), 1)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        (AdjustedImage, [Fit(width=50)], 'storage_path'),))
    def test_preadjust__empty(self):
        preadjust = Preadjust()
        storage_path = 'does_not_exist.png'
        AdjustedImage.objects.create(storage_path=storage_path,
                                     adjusted=storage_path)
        self.assertEqual(AdjustedImage.objects.count(), 1)

        preadjust.stdout = mock.MagicMock()
        preadjust._preadjust()
        preadjust.stdout.write.assert_has_calls([
            mock.call('Skipped 1 empty path.\n'),
            mock.call('Skipped 0 paths which have already been adjusted.\n'),
            mock.call('No paths remaining to adjust.\n'),
        ])

        self.assertEqual(AdjustedImage.objects.count(), 1)

    @override_settings(DAGUERRE_PREADJUSTMENTS=(
        (AdjustedImage, [Fit(width=50)], 'storage_path'),))
    def test_preadjust__skipped(self):
        preadjust = Preadjust()
        storage_path = self.create_image('100x100.png')
        AdjustedImage.objects.create(storage_path=storage_path,
                                     adjusted=storage_path,
                                     requested='fit|50|')
        self.assertEqual(AdjustedImage.objects.count(), 1)

        preadjust.stdout = mock.MagicMock()
        preadjust._preadjust()
        preadjust.stdout.write.assert_has_calls([
            mock.call('Skipped 0 empty paths.\n'),
            mock.call('Skipped 1 path which has already been adjusted.\n'),
            mock.call('No paths remaining to adjust.\n'),
        ])

        self.assertEqual(AdjustedImage.objects.count(), 1)

    def test_preadjust__generate(self):
        preadjust = Preadjust()
        storage_path = self.create_image('100x100.png')
        self.assertEqual(AdjustedImage.objects.count(), 0)

        preadjust.stdout = mock.MagicMock()

        dp = (([storage_path], [Fit(width=50)], None),)
        with override_settings(DAGUERRE_PREADJUSTMENTS=dp):
            preadjust._preadjust()
        preadjust.stdout.write.assert_has_calls([
            mock.call('Skipped 0 empty paths.\n'),
            mock.call('Skipped 0 paths which have already been adjusted.\n'),
            mock.call('Adjusting 1 path... '),
            mock.call('Done.\n'),
        ])

        self.assertEqual(AdjustedImage.objects.count(), 1)

    def test_preadjust__generate__failed(self):
        preadjust = Preadjust()
        storage_path = self.create_image('100x100.png')
        self.assertEqual(AdjustedImage.objects.count(), 0)

        preadjust.stdout = mock.MagicMock()

        dp = (([storage_path], [Fit(width=50)], None),)
        with override_settings(DAGUERRE_PREADJUSTMENTS=dp):
            with mock.patch('daguerre.helpers.save_image', side_effect=IOError):
                preadjust._preadjust()
        preadjust.stdout.write.assert_has_calls([
            mock.call('Skipped 0 empty paths.\n'),
            mock.call('Skipped 0 paths which have already been adjusted.\n'),
            mock.call('Adjusting 1 path... '),
            mock.call('Done.\n'),
            mock.call('1 path failed due to I/O errors.')
        ])

        self.assertEqual(AdjustedImage.objects.count(), 0)


class DaguerreTestCase(BaseTestCase):
    def test_find_commands(self):
        daguerre_command = Daguerre()
        self.assertEqual(daguerre_command._find_commands(), {
            'clean': '_daguerre_clean',
            'preadjust': '_daguerre_preadjust'
        })
