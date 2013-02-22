from django.http import Http404
from django.test import RequestFactory

from daguerre.tests.base import BaseTestCase
from daguerre.utils.adjustments import AdjustmentHelper
from daguerre.views import AdjustedImageRedirectView, AjaxAdjustmentInfoView


class AdjustedImageRedirectViewTestCase(BaseTestCase):
	def setUp(self):
		self.view = AdjustedImageRedirectView()
		super(AdjustedImageRedirectViewTestCase, self).setUp()

	def test_check_security(self):
		"""A 404 should be raised if the security hash is missing or incorrect."""
		storage_path = 'path/to/thing.jpg'
		helper = AdjustmentHelper(storage_path, width=10, height=5, crop='face')
		factory = RequestFactory()
		self.view.kwargs = {'storage_path': storage_path}

		get_params = {}
		self.view.request = factory.get('/', get_params)
		self.assertRaises(Http404, self.view.get_helper)

		get_params = {AdjustmentHelper.param_map['security']: 'fake!'}
		self.view.request = factory.get('/', get_params)
		self.assertRaises(Http404, self.view.get_helper)

		get_params = helper.to_querydict(secure=True)
		self.view.request = factory.get('/', get_params)

	def test_nonexistant(self):
		"""
		A 404 should be raised if the original image doesn't exist.

		"""
		factory = RequestFactory()
		storage_path = 'nonexistant.png'
		helper = AdjustmentHelper(storage_path, width=10, height=10)
		self.view.kwargs = {'storage_path': storage_path}
		self.view.request = factory.get('/', helper.to_querydict(secure=True))
		self.assertRaises(Http404, self.view.get, self.view.request)


class AjaxAdjustmentInfoViewTestCase(BaseTestCase):
	def setUp(self):
		self.view = AjaxAdjustmentInfoView()
		super(AjaxAdjustmentInfoViewTestCase, self).setUp()

	def test_nonexistant(self):
		"""
		A 404 should be raised if the original image doesn't exist.

		"""
		factory = RequestFactory()
		storage_path = 'nonexistant.png'
		helper = AdjustmentHelper(storage_path, width=10, height=5)
		self.view.kwargs = {'storage_path': storage_path}
		get_params = helper.to_querydict()
		self.view.request = factory.get('/', get_params,
							  			HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertRaises(Http404, self.view.get, self.view.request)
