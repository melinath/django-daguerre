import json

from django.core.exceptions import ValidationError
from django.http import (HttpResponse, Http404, HttpResponseRedirect,
                         HttpResponseForbidden)
from django.views.generic import View

from daguerre.helpers import AdjustmentHelper
from daguerre.models import Area


class AdjustedImageRedirectView(View):
    """
    Returns a redirect to an :attr:`~AdjustedImage.adjusted` file,
    first creating the :class:`~AdjustedImage` if necessary.

    :param storage_path: The path to the original image file,
    relative to the default storage.
    """
    secure = True

    def get_helper(self):
        try:
            return AdjustmentHelper.from_querydict(
                self.kwargs['storage_path'],
                self.request.GET,
                secure=self.secure)
        except ValueError, e:
            raise Http404(e.message)

    def get(self, request, *args, **kwargs):
        helper = self.get_helper()
        try:
            adjusted = helper.adjust()
        except IOError, e:
            raise Http404(e.message)
        return HttpResponseRedirect(adjusted.adjusted.url)


class AjaxAdjustmentInfoView(AdjustedImageRedirectView):
    """Returns a JSON response containing the results of a call to
    :meth:`.Adjustment.info_dict` for the given parameters."""
    secure = False

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404("Request is not AJAX.")

        helper = self.get_helper()
        info_dict = helper.info_dict()

        if not info_dict:
            # Something went wrong. The image probably doesn't exist.
            raise Http404

        return HttpResponse(
            json.dumps(info_dict),
            content_type="application/json")


class AjaxUpdateAreaView(View):
    def has_add_permission(self, request):
        opts = Area._meta
        return request.user.has_perm(
            opts.app_label + '.' + opts.get_add_permission())

    def has_change_permission(self, request):
        opts = Area._meta
        return request.user.has_perm(
            opts.app_label + '.' + opts.get_change_permission())

    def has_delete_permission(self, request):
        opts = Area._meta
        return request.user.has_perm(
            opts.app_label + '.' + opts.get_delete_permission())

    def get(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404("Request is not AJAX.")

        storage_path = self.kwargs['storage_path']

        if self.kwargs['pk'] is not None:
            try:
                area = Area.objects.get(storage_path=storage_path,
                                        pk=self.kwargs['pk'])
            except Area.DoesNotExist:
                raise Http404

            data = area.serialize()
        else:
            areas = Area.objects.filter(storage_path=storage_path)
            data = [area.serialize() for area in areas]
        return HttpResponse(json.dumps(data), content_type="application/json")

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404("Request is not AJAX.")

        if not self.has_change_permission(request):
            return HttpResponseForbidden('')

        storage_path = self.kwargs['storage_path']
        data = {
            'name': request.POST.get('name') or '',
        }
        for int_field in ('x1', 'x2', 'y1', 'y2', 'priority'):
            try:
                data[int_field] = int(request.POST.get(int_field))
            except (ValueError, TypeError):
                raise Http404

        try:
            area = Area.objects.get(storage_path=storage_path,
                                    pk=self.kwargs['pk'])
        except Area.DoesNotExist:
            if not self.has_add_permission(request):
                return HttpResponseForbidden('')
            area = Area(storage_path=storage_path, **data)
        else:
            for fname, value in data.iteritems():
                setattr(area, fname, value)

        status = 200
        try:
            area.full_clean()
        except ValidationError, e:
            data = {'error': e.message_dict}
            status = 400
        else:
            area.save()
            data = area.serialize()

        return HttpResponse(json.dumps(data),
                            content_type="application/json",
                            status=status)

    def delete(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404("Request is not AJAX.")

        if self.kwargs['pk'] is None:
            raise Http404("No pk was provided.")

        if not self.has_delete_permission(request):
            return HttpResponseForbidden('')

        Area.objects.filter(storage_path=self.kwargs['storage_path'],
                            pk=self.kwargs['pk']).delete()

        return HttpResponse('')
