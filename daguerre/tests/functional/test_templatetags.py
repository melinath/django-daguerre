from django.template import Template, Context

from daguerre.models import AdjustedImage
from daguerre.tests.base import BaseTestCase
from daguerre.utils.adjustments import AdjustmentHelper


class AdjustTemplatetagTestCase(BaseTestCase):
    def test_path(self):
        """Tag should accept a path as its argument."""
        storage_path = self.create_image('100x100.png')
        helper = AdjustmentHelper(storage_path, width=50, height=50,
                                  adjustment='fit')
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' %}")
        c = Context({'image': storage_path})
        self.assertEqual(t.render(c), helper.info_dict()['url'])

    def test_file(self):
        """Tag should accept an :class:`ImageFieldFile` as its argument."""
        storage_path = self.create_image('100x100.png')
        adjusted = AdjustedImage()
        adjusted.adjusted = storage_path
        helper = AdjustmentHelper(storage_path, width=50, height=50,
                                  adjustment='fit')
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' %}")
        c = Context({'image': adjusted.adjusted})
        self.assertEqual(t.render(c), helper.info_dict()['url'])

    def test_invalid(self):
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' %}")
        c = Context({'image': 23})
        self.assertEqual(t.render(c), '')
