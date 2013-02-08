from django.template import Template, Context
from django.test import TestCase

from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator
from daguerre.utils.adjustments import AdjustmentHelper


class AdjustTemplatetagTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		self.image_creator = ImageCreator()
		super(AdjustTemplatetagTestCase, self).setUp()

	def test_path(self):
		"""Tag should accept a path as its argument."""
		image = self.image_creator.create('100x100.png')
		helper = AdjustmentHelper(image, width=50, height=50, adjustment='fit')
		t = Template("{% load daguerre %}{% adjust image width=50 height=50 adjustment='fit' %}")
		c = Context({'image': image.image.name})
		self.assertEqual(t.render(c), helper.info_dict()['url'])

	def test_file(self):
		"""Tag should accept an :class:`ImageFile` as its argument."""
		image = self.image_creator.create('100x100.png')
		helper = AdjustmentHelper(image, width=50, height=50, adjustment='fit')
		t = Template("{% load daguerre %}{% adjust image width=50 height=50 adjustment='fit' %}")
		c = Context({'image': image.image})
		self.assertEqual(t.render(c), helper.info_dict()['url'])

	def test_invalid(self):
		t = Template("{% load daguerre %}{% adjust image width=50 height=50 adjustment='fit' %}")
		c = Context({'image': 23})
		self.assertEqual(t.render(c), '')
