from django.core.files.storage import default_storage
from django.http import Http404
from django.test import TestCase, RequestFactory

from daguerre.models import Image
from daguerre.tests.base import DaguerreTestCaseMixin, ImageCreator
from daguerre.utils import make_security_hash
from daguerre.utils.adjustments import QUERY_PARAMS, DEFAULT_ADJUSTMENT
from daguerre.views import BaseAdjustmentView, AdjustedImageRedirectView, AjaxAdjustmentInfoView


class BaseAdjustmentViewTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		TestCase.setUp(self)
		self.view = BaseAdjustmentView()

	def test_get_adjustment_kwargs(self):
		"""Missing parameters should be ignored; integer parameters should be ignored if empty or converted to integers otherwise. Integer parameters which can't be converted cause a 404 to be raised. Adjustment defaults to :data:`.DEFAULT_ADJUSTMENT` if not provided."""
		factory = RequestFactory()
		get_params = {
			QUERY_PARAMS['width']: '',
			QUERY_PARAMS['height']: '',
			QUERY_PARAMS['max_width']: '',
			QUERY_PARAMS['max_height']: '',
		}
		self.view.request = factory.get('/', get_params)
		kwargs = self.view.get_adjustment_kwargs()
		self.assertEqual(kwargs, {'adjustment': DEFAULT_ADJUSTMENT})

		get_params = {
			QUERY_PARAMS['width']: '10',
			QUERY_PARAMS['height']: 5,
			QUERY_PARAMS['crop']: 'none',
			QUERY_PARAMS['adjustment']: 'crop'
		}
		self.view.request = factory.get('/', get_params)
		kwargs = self.view.get_adjustment_kwargs()
		self.assertEqual(kwargs, {'width': 10, 'height': 5, 'crop': 'none', 'adjustment': 'crop'})

	def test_get_image(self):
		"""get_image returns an image for a storage path or raises 404."""
		image_creator = ImageCreator()
		self.view.kwargs = {'storage_path': 'nonexistant.png'}
		self.assertRaises(Http404, self.view.get_image)
		fp = default_storage.open('totally-an-image.jpg', 'w')
		fp.write('hi')
		fp.close()
		self.view.kwargs['storage_path'] = 'totally-an-image.jpg'
		self.assertRaises(Http404, self.view.get_image)

		image = image_creator.create('100x100.png')
		self.view.kwargs['storage_path'] = image.image.name
		result = self.view.get_image()
		self.assertEqual(result, image)


class AdjustedImageRedirectViewTestCase(DaguerreTestCaseMixin, TestCase):
	def setUp(self):
		TestCase.setUp(self)
		self.view = AdjustedImageRedirectView()

	def test_check_security(self):
		"""A 404 should be raised if the security hash is missing or incorrect."""
		adjustment_kwargs = {
			'width': 10,
			'height': 5,
			'crop': 'face',
		}
		factory = RequestFactory()
		self.view.kwargs = {'storage_path': 'path/to/thing.jpg'}

		get_params = {}
		self.view.request = factory.get('/', get_params)
		self.assertRaises(Http404, self.view.check_security, adjustment_kwargs)

		get_params = {QUERY_PARAMS['security']: 'fake!'}
		self.view.request = factory.get('/', get_params)
		self.assertRaises(Http404, self.view.check_security, adjustment_kwargs)

		get_params = {QUERY_PARAMS['security']: make_security_hash(self.view.kwargs['storage_path'], *[adjustment_kwargs.get(k) for k in self.view.params])}
		self.view.request = factory.get('/', get_params)
		# I wish we had an assertNotRaises...
		self.assertTrue(self.view.check_security(adjustment_kwargs) is None)
