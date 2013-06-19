from daguerre.adjustments import Crop
from daguerre.helpers import AdjustmentHelper
from daguerre.tests.base import BaseTestCase


class RequestResponseTestCase(BaseTestCase):
    def test_unprepped(self):
        image = self.create_image('100x100.png')

        crop = Crop(width=50, height=50)

        with self.assertNumQueries(1):
            info_dict = AdjustmentHelper([image], [crop]).info_dicts()[0][1]
        with self.assertNumQueries(4):
            response = self.client.get(info_dict['url'])
        self.assertEqual(response.status_code, 302)

    def test_prepped(self):
        image = self.create_image('100x100.png')

        crop = Crop(width=50, height=50)

        with self.assertNumQueries(1):
            info_dict = AdjustmentHelper([image], [crop]).info_dicts()[0][1]
        with self.assertNumQueries(4):
            AdjustmentHelper([image], [crop]).adjust()
        with self.assertNumQueries(1):
            response = self.client.get(info_dict['url'])
        self.assertEqual(response.status_code, 302)

    def test_preprepped(self):
        image = self.create_image('100x100.png')

        crop = Crop(width=50, height=50)

        helper = AdjustmentHelper([image], [crop])
        with self.assertNumQueries(4):
            helper.adjust()
        adjusted = list(helper.adjusted.values())[0]

        with self.assertNumQueries(1):
            info_dict = AdjustmentHelper([image], [crop]
                                         ).info_dicts()[0][1]
        self.assertEqual(info_dict['url'], adjusted['url'])
