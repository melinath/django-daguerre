import json

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import View

from daguerre.models import Image
from daguerre.utils.adjustments import AdjustmentHelper


class AdjustedImageRedirectView(View):
	"""
	Returns a redirect to an :attr:`~AdjustedImage.adjusted` file, first creating the :class:`~AdjustedImage` if necessary.

	:param storage_path: The path to the original image file, relative to the default storage.

	"""
	secure = True

	def get_helper(self):
		try:
			return AdjustmentHelper.from_querydict(self.kwargs['storage_path'], self.request.GET, secure=self.secure)
		except ValueError, e:
			raise Http404(e.message)

	def get(self, request, *args, **kwargs):
		helper = self.get_helper()
		try:
			adjusted = helper.adjust()
		except (IOError, Image.DoesNotExist), e:
			raise Http404(e.message)
		return HttpResponseRedirect(adjusted.adjusted.url)


class AjaxAdjustmentInfoView(AdjustedImageRedirectView):
	"""Returns a JSON response containing the results of a call to :meth:`.Adjustment.info_dict` for the given parameters."""
	secure = False

	def get(self, request, *args, **kwargs):
		if not request.is_ajax():
			raise Http404("Request is not AJAX.")

		helper = self.get_helper()
		info_dict = helper.info_dict()

		if not info_dict:
			# Something went wrong. The image probably doesn't exist.
			raise Http404

		return HttpResponse(json.dumps(info_dict), mimetype="application/json")
