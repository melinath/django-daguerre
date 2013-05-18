from django.template import Template, Context
from django.utils.html import escape

from daguerre.adjustments import Fit
from daguerre.helpers import AdjustmentHelper
from daguerre.models import AdjustedImage
from daguerre.tests.base import BaseTestCase


class AdjustTemplatetagTestCase(BaseTestCase):
    def test_path(self):
        """Tag should accept a path as its argument."""
        storage_path = self.create_image('100x100.png')
        helper = AdjustmentHelper([storage_path], None,
                                  Fit(width=50, height=50))
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' %}")
        c = Context({'image': storage_path})
        self.assertEqual(t.render(c), escape(helper.info_dicts()[0][1]['url']))

    def test_file(self):
        """Tag should accept an :class:`ImageFieldFile` as its argument."""
        storage_path = self.create_image('100x100.png')
        adjusted = AdjustedImage()
        adjusted.adjusted = storage_path
        helper = AdjustmentHelper([storage_path], None,
                                  Fit(width=50, height=50))
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' as adj %}{{ adj }}")
        c = Context({'image': adjusted.adjusted})
        self.assertEqual(t.render(c), escape(helper.info_dicts()[0][1]['url']))

    def test_invalid(self):
        t = Template("{% load daguerre %}{% adjust image width=50 height=50 "
                     "adjustment='fit' %}")
        c = Context({'image': 23})
        self.assertEqual(t.render(c), '')


class BulkTestObject(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path


class AdjustBulkTemplatetagTestCase(BaseTestCase):
    def test_paths(self):
        """Tag should accept an iterable of objects with paths."""
        objs = [
            BulkTestObject(self.create_image('100x100.png'))
        ]
        helper = AdjustmentHelper(objs, 'storage_path',
                                  Fit(width=50, height=50))
        t = Template("{% load daguerre %}{% adjust_bulk objs 'storage_path' "
                     "width=50 height=50 adjustment='fit' as bulk %}"
                     "{{ bulk.0.1 }}")
        c = Context({'objs': objs})
        self.assertEqual(t.render(c),
                         escape(helper.info_dicts()[0][1]['url']))
