import os

from django.contrib.auth.models import User, Permission
from django.test import TestCase
try:
    from PIL import ImageChops, Image
except ImportError:
    import Image
    import ImageChops

import daguerre
from daguerre.models import Area
from daguerre.utils import save_image


TEST_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(daguerre.__file__), 'tests', 'data')
)


class BaseTestCase(TestCase):
    @classmethod
    def _data_path(cls, test_path):
        """Given a path relative to daguerre/tests/data/,
        returns an absolute path."""
        return os.path.join(TEST_DATA_DIR, test_path)

    @classmethod
    def _data_file(cls, test_path, mode='r'):
        """Given a path relative to daguerre/tests/data/,
        returns an open file."""
        return open(cls._data_path(test_path), mode)

    def assertImageEqual(self, im1, im2):
        # First check that they're the same size. A difference
        # comparison could pass for images of different sizes.
        self.assertEqual(im1.size, im2.size)
        # Image comparisons according to
        # http://effbot.org/zone/pil-comparing-images.htm
        self.assertTrue(ImageChops.difference(im1, im2).getbbox() is None)

    def create_image(self, test_path):
        image = Image.open(self._data_path(test_path))
        return save_image(image, 'daguerre/test/{0}'.format(test_path))

    def create_area(
            self,
            test_path='100x100.png',
            x1=0,
            y1=0,
            x2=100,
            y2=100,
            **kwargs):
        if 'storage_path' not in kwargs:
            kwargs['storage_path'] = self.create_image(test_path)
        kwargs.update({
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2
        })
        return Area.objects.create(**kwargs)

    def create_user(
            self,
            username='test',
            password='test',
            permissions=None,
            **kwargs):
        user = User(username=username, **kwargs)
        user.set_password(password)
        user.save()

        if permissions:
            for permission in permissions:
                app_label, codename = permission.split('.')
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename)
                user.user_permissions.add(permission)

        return user
