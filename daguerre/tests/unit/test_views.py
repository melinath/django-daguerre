import json

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import RequestFactory
from django.utils.encoding import force_text

from daguerre.helpers import AdjustmentHelper
from daguerre.models import Area
from daguerre.tests.base import BaseTestCase
from daguerre.views import (AdjustedImageRedirectView, AjaxAdjustmentInfoView,
                            AjaxUpdateAreaView)


class AdjustedImageRedirectViewTestCase(BaseTestCase):
    def setUp(self):
        self.view = AdjustedImageRedirectView()
        super(AdjustedImageRedirectViewTestCase, self).setUp()

    def test_check_security(self):
        """
        A 404 should be raised if the security hash is missing or incorrect.

        """
        storage_path = 'path/to/thing.jpg'
        helper = AdjustmentHelper([storage_path])
        helper.adjust('namedcrop', name='face')
        helper.adjust('fill', width=10, height=5)
        factory = RequestFactory()
        self.view.kwargs = {'storage_path': storage_path}

        get_params = {}
        self.view.request = factory.get('/', get_params)
        self.assertRaises(Http404, self.view.get_helper)

        get_params = {AdjustmentHelper.query_map['security']: 'fake!'}
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
        helper = AdjustmentHelper([storage_path])
        helper.adjust('fill', width=10, height=10)
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
        helper = AdjustmentHelper([storage_path])
        helper.adjust('fill', width=10, height=5)
        self.view.kwargs = {'storage_path': storage_path}
        get_params = helper.to_querydict()
        self.view.request = factory.get('/', get_params,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertRaises(Http404, self.view.get, self.view.request)


class AjaxUpdateAreaViewTestCase(BaseTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        super(AjaxUpdateAreaViewTestCase, self).setUp()

    def test_not_ajax(self):
        request = self.factory.get('/')
        view = AjaxUpdateAreaView()
        self.assertRaises(Http404, view.get, request)
        self.assertRaises(Http404, view.post, request)
        self.assertRaises(Http404, view.delete, request)

    def test_get__pk(self):
        area = self.create_area(x2=50, y2=50)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }
        request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        with self.assertNumQueries(1):
            response = view.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(force_text(response.content))
        self.assertEqual(data, area.serialize())

    def test_get__pk__wrong(self):
        area = self.create_area(x2=50, y2=50)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk + 1,
        }
        request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        with self.assertNumQueries(1):
            self.assertRaises(Http404, view.get, request)

    def test_get__no_pk(self):
        area1 = self.create_area(x2=50, y2=50)
        area2 = self.create_area(x2=50, y2=50, storage_path=area1.storage_path)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area1.storage_path,
            'pk': None
        }
        request = self.factory.get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        with self.assertNumQueries(1):
            response = view.get(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(force_text(response.content))
        self.assertEqual(data, [area1.serialize(), area2.serialize()])

    def test_post__no_change_perms(self):
        view = AjaxUpdateAreaView()
        request = self.factory.post('/',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        self.assertFalse(request.user.has_perm('daguerre.change_area'))
        with self.assertNumQueries(0):
            response = view.post(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(force_text(response.content), '')

    def test_post__invalid_params(self):
        area = self.create_area(x2=50, y2=50)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }

        params = {
            'x1': 0,
            'y1': 0,
            'x2': 50,
            'y2': 50,
            'priority': 3,
        }
        user = self.create_user(permissions=['daguerre.change_area'])
        self.assertTrue(user.has_perm('daguerre.change_area'))
        for key in params:
            params_copy = params.copy()
            params_copy[key] = 'hi'
            request = self.factory.post('/', params_copy,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            request.user = user
            with self.assertNumQueries(0):
                self.assertRaises(Http404, view.post, request)

    def test_post__update(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        old_serialize = area.serialize()
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }

        params = {
            'x1': 50,
            'y1': 50,
            'x2': 100,
            'y2': 100,
            'priority': 1,
            'name': 'fun'
        }
        request = self.factory.post('/', params,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.change_area'])
        self.assertTrue(request.user.has_perm('daguerre.change_area'))
        # SB: Used to assert 4 - don't remember why.
        # Three queries expected: get the area, update the area,
        # and clear the adjustment cache.
        with self.assertNumQueries(3):
            response = view.post(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        self.assertEqual(Area.objects.count(), 1)
        data = json.loads(force_text(response.content))
        new_area = Area.objects.get(pk=area.pk, storage_path=area.storage_path)
        self.assertEqual(data, new_area.serialize())
        self.assertNotEqual(data, old_serialize)
        del data['storage_path']
        del data['id']
        self.assertEqual(data, params)

    def test_post__update__invalid(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }

        params = {
            'x1': 100,
            'y1': 50,
            'x2': 50,
            'y2': 100,
            'priority': 1,
            'name': 'fun'
        }
        request = self.factory.post('/', params,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.change_area'])
        self.assertTrue(request.user.has_perm('daguerre.change_area'))
        with self.assertNumQueries(1):
            response = view.post(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Area.objects.count(), 1)
        data = json.loads(force_text(response.content))
        self.assertEqual(list(data.keys()), ['error'])

    def test_post__add(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': None,
        }

        params = {
            'x1': 50,
            'y1': 50,
            'x2': 100,
            'y2': 100,
            'priority': 1,
            'name': 'fun'
        }
        request = self.factory.post('/', params,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.change_area',
                                                     'daguerre.add_area'])
        self.assertTrue(request.user.has_perm('daguerre.change_area'))
        self.assertTrue(request.user.has_perm('daguerre.add_area'))
        with self.assertNumQueries(3):
            response = view.post(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        self.assertEqual(Area.objects.count(), 2)
        data = json.loads(force_text(response.content))
        new_area = Area.objects.exclude(pk=area.pk).get()
        self.assertEqual(data, new_area.serialize())
        del data['storage_path']
        del data['id']
        self.assertEqual(data, params)

    def test_post__add__no_perms(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': None,
        }

        params = {
            'x1': 50,
            'y1': 50,
            'x2': 100,
            'y2': 100,
            'priority': 1,
            'name': 'fun'
        }
        request = self.factory.post('/', params,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.change_area'])
        self.assertTrue(request.user.has_perm('daguerre.change_area'))
        with self.assertNumQueries(1):
            response = view.post(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Area.objects.count(), 1)
        self.assertEqual(force_text(response.content), '')

    def test_delete__no_perms(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }

        request = self.factory.delete('/',
                                      HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = AnonymousUser()
        self.assertFalse(request.user.has_perm('daguerre.delete_area'))
        with self.assertNumQueries(0):
            response = view.delete(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Area.objects.count(), 1)
        self.assertEqual(force_text(response.content), '')

    def test_delete__no_pk(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': None,
        }

        request = self.factory.delete('/',
                                      HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.delete_area'])
        self.assertTrue(request.user.has_perm('daguerre.delete_area'))
        with self.assertNumQueries(0):
            self.assertRaises(Http404, view.delete, request)

        self.assertEqual(Area.objects.count(), 1)

    def test_delete(self):
        area = self.create_area(x2=50, y2=50)
        self.assertEqual(Area.objects.count(), 1)
        view = AjaxUpdateAreaView()
        view.kwargs = {
            'storage_path': area.storage_path,
            'pk': area.pk,
        }

        request = self.factory.delete('/',
                                      HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.create_user(permissions=['daguerre.delete_area'])
        self.assertTrue(request.user.has_perm('daguerre.delete_area'))
        with self.assertNumQueries(3):
            response = view.delete(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(force_text(response.content), '')
        self.assertEqual(Area.objects.count(), 0)
