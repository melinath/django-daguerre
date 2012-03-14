import json

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import View

from daguerre.models import Image, AdjustedImage
from daguerre.utils import check_security_hash
from daguerre.utils.adjustments import get_adjustment_class, DEFAULT_ADJUSTMENT, QUERY_PARAMS


class BaseAdjustmentView(View):
	int_params = set(('width', 'height', 'max_width', 'max_height'))
	params = ('width', 'height', 'max_width', 'max_height', 'adjustment', 'crop')

	def get_adjustment_kwargs(self):
		"""Returns a dictionary of arguments which can be used to make an image adjustment."""
		kwargs = {}
		for key in self.params:
			get_key = QUERY_PARAMS[key]
			try:
				value = self.request.GET[get_key]
			except KeyError:
				continue

			if key in self.int_params:
				if value == '':
					continue
				try:
					value = int(value)
				except ValueError, e:
					raise Http404(e.message)

			kwargs[key] = value

		kwargs['adjustment'] = kwargs.get('adjustment', DEFAULT_ADJUSTMENT)
		return kwargs

	def get_image(self):
		"""Returns an image for the storage path or raises 404."""
		try:
			return Image.objects.for_storage_path(self.kwargs['storage_path'])
		except Image.DoesNotExist, e:
			raise Http404(e.message)


class AdjustedImageRedirectView(BaseAdjustmentView):
	"""
	Returns a redirect to an :attr:`~AdjustedImage.adjusted` file, first creating the :class:`~AdjustedImage` if necessary.

	:param storage_path: The path to the original image file, relative to the default storage.

	"""
	def check_security(self, adjustment_kwargs):
		"""Checks whether the request passes a security test, and raises a 404 otherwise."""
		get_key = QUERY_PARAMS['security']
		try:
			security = self.request.GET[get_key]
		except KeyError:
			raise Http404("Security hash missing.")

		if not check_security_hash(security, self.kwargs['storage_path'], *[adjustment_kwargs.get(k) for k in self.params]):
			raise Http404("Security check failed.")

	def get(self, request, *args, **kwargs):
		adjustment_kwargs = self.get_adjustment_kwargs()
		self.check_security(adjustment_kwargs)
		image = self.get_image()
		adjusted = AdjustedImage.objects.adjust(image, **adjustment_kwargs)
		return HttpResponseRedirect(adjusted.adjusted.url)


class AjaxAdjustmentInfoView(BaseAdjustmentView):
	"""Returns a JSON response containing the results of a call to :meth:`.Adjustment.info_dict` for the given parameters."""
	def get(self, request, *args, **kwargs):
		if not request.is_ajax():
			raise Http404("Request is not AJAX.")

		adjustment_kwargs = self.get_adjustment_kwargs()
		image = self.get_image()
		adjustment_class = get_adjustment_class(adjustment_kwargs.pop('adjustment'))
		adjustment = adjustment_class.from_image(image, **adjustment_kwargs)
		return HttpResponse(json.dumps(adjustment.info_dict()), mimetype="application/json")
