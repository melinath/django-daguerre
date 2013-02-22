from daguerre.tests.base import BaseTestCase
from daguerre.utils.adjustments import AdjustmentHelper


class RequestResponseTestCase(BaseTestCase):
	def test_unprepped(self):
		image = self.create_image('100x100.png')

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		with self.assertNumQueries(1):
			info_dict = AdjustmentHelper(image, **kwargs).info_dict()
		with self.assertNumQueries(4):
			response = self.client.get(info_dict['url'])
		self.assertEqual(response.status_code, 302)

	def test_prepped(self):
		image = self.create_image('100x100.png')

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		with self.assertNumQueries(1):
			info_dict = AdjustmentHelper(image, **kwargs).info_dict()
		with self.assertNumQueries(4):
			AdjustmentHelper(image, **kwargs).adjust()
		with self.assertNumQueries(1):
			response = self.client.get(info_dict['url'])
		self.assertEqual(response.status_code, 302)

	def test_preprepped(self):
		image = self.create_image('100x100.png')

		kwargs = {
			'width': 50,
			'height': 50,
			'adjustment': 'crop',
		}

		with self.assertNumQueries(4):
			adjusted = AdjustmentHelper(image, **kwargs).adjust()
		with self.assertNumQueries(1):
			info_dict = AdjustmentHelper(image, **kwargs).info_dict()
		self.assertEqual(info_dict['url'], adjusted.adjusted.url)
