from django.template import Template, Context
from django.utils.html import escape

from daguerre.adjustments import Fit, Crop
from daguerre.helpers import AdjustmentHelper
from daguerre.models import AdjustedImage
from daguerre.tests.base import BaseTestCase


class AdjustTemplatetagTestCase(BaseTestCase):
    def test_path(self):
        # Tag should accept a path as its argument.
        storage_path = self.create_image('100x100.png')
        helper = AdjustmentHelper([storage_path], [Fit(width=50, height=50)])
        t = Template("{% load daguerre %}{% adjust image 'fit' width=50 "
                     "height=50 %}")
        c = Context({'image': storage_path})
        self.assertEqual(t.render(c), escape(helper.info_dicts()[0][1]['url']))

    def test_file(self):
        # Tag should accept an :class:`ImageFieldFile` as its argument.
        storage_path = self.create_image('100x100.png')
        adjusted = AdjustedImage()
        adjusted.adjusted = storage_path
        helper = AdjustmentHelper([storage_path], [Fit(width=50, height=50)])
        t = Template("{% load daguerre %}{% adjust image 'fit' width=50 "
                     "height=50 as adj %}{{ adj }}")
        c = Context({'image': adjusted.adjusted})
        self.assertEqual(t.render(c), escape(helper.info_dicts()[0][1]['url']))

    def test_invalid(self):
        t = Template("{% load daguerre %}{% adjust image 'fit' width=50 "
                     "height=50 %}")
        c = Context({'image': 23})
        self.assertEqual(t.render(c), '')

    def test_multiple(self):
        # Tag should allow multiple adjustments to be passed in.
        storage_path = self.create_image('100x100.png')
        helper = AdjustmentHelper([storage_path], [Crop(width=50, height=50),
                                                   Fit(width=25)])
        t = Template("{% load daguerre %}{% adjust image 'crop' width=50 "
                     "height=50 'fit' width=25 %}")
        c = Context({'image': storage_path})
        self.assertEqual(t.render(c), escape(helper.info_dicts()[0][1]['url']))


class BulkTestObject(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path


class AdjustBulkTemplatetagTestCase(BaseTestCase):
    def test_paths(self):
        # Tag should accept an iterable of objects with paths.
        objs = [
            BulkTestObject(self.create_image('100x100.png'))
        ]
        helper = AdjustmentHelper(objs, [Fit(width=50, height=50)],
                                  'storage_path')
        t = Template("{% load daguerre %}{% adjust_bulk objs 'storage_path' "
                     "'fit' width=50 height=50 as bulk %}"
                     "{{ bulk.0.1 }}")
        c = Context({'objs': objs})
        self.assertEqual(t.render(c),
                         escape(helper.info_dicts()[0][1]['url']))

    def test_multiple(self):
        # Tag should accept multiple adjustments.
        objs = [
            BulkTestObject(self.create_image('100x100.png'))
        ]
        helper = AdjustmentHelper(objs,
                                  [Crop(width=50, height=50),
                                   Fit(width=25)],
                                  'storage_path')
        t = Template("{% load daguerre %}{% adjust_bulk objs 'storage_path' "
                     "'crop' width=50 height=50 'fit' width=25 as bulk %}"
                     "{{ bulk.0.1 }}")
        c = Context({'objs': objs})
        self.assertEqual(t.render(c),
                         escape(helper.info_dicts()[0][1]['url']))

    def test_no_lookups(self):
        # Tag should accept an iterable of paths.
        paths = [
            self.create_image('100x100.png')
        ]
        helper = AdjustmentHelper(paths,
                                  [Fit(width=50, height=50)])
        t = Template("{% load daguerre %}{% adjust_bulk paths 'fit' "
                     "width=50 height=50 as bulk %}{{ bulk.0.1 }}")
        c = Context({'paths': paths})
        self.assertEqual(t.render(c),
                         escape(helper.info_dicts()[0][1]['url']))
