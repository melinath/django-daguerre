import json

from django.http import HttpResponse, Http404, HttpResponseRedirect

from daguerre.middleware import private_ajax
from daguerre.models import Image, AdjustedImage
from daguerre.utils import check_security_hash
from daguerre.utils.adjustments import get_adjustment_class, DEFAULT_ADJUSTMENT, QUERY_PARAMS


def clean_dim(dim):
	if dim is not None:
		try:
			dim = int(dim)
		except ValueError:
			raise Http404
	return dim


def adjusted_image_redirect(request, storage_path):
	"""
	Returns a redirect to an :attr:`~AdjustedImage.adjusted` file, first creating the :class:`~AdjustedImage` if necessary.

	:param storage_path: The path to the original image file, relative to the default storage.

	"""
	kwargs = {}

	for key in ('width', 'height', 'max_width', 'max_height', 'crop', 'adjustment', 'security'):
		get_key = QUERY_PARAMS[key]
		try:
			kwargs[key] = request.GET[get_key]
		except KeyError:
			pass

	for key in ('width', 'height', 'max_width', 'max_height'):
		try:
			kwargs[key] = clean_dim(kwargs[key])
		except KeyError:
			pass

	try:
		security = kwargs.pop('security')
	except KeyError:
		raise Http404("Security hash missing.")

	kwargs['adjustment'] = kwargs.get('adjustment', DEFAULT_ADJUSTMENT)

	if not check_security_hash(security, storage_path, *[kwargs.get(key) for key in ('width', 'height', 'max_width', 'max_height', 'adjustment', 'crop')]):
		raise Http404("Security check failed.")

	image = Image.objects.for_storage_path(storage_path)

	# Once you have the Image, adjust it!
	adjusted = AdjustedImage.objects.adjust(image, **kwargs)

	return HttpResponseRedirect(adjusted.adjusted.url)


@private_ajax
def ajax_adjustment_info(request, storage_path):
	if not request.is_ajax():
		raise Http404("Request is not AJAX.")

	kwargs = {}

	for key in ('width', 'height', 'max_width', 'max_height', 'crop', 'adjustment'):
		get_key = QUERY_PARAMS[key]
		try:
			kwargs[key] = request.GET[get_key]
		except KeyError:
			pass

	for key in ('width', 'height', 'max_width', 'max_height'):
		try:
			kwargs[key] = clean_dim(kwargs[key])
		except KeyError:
			pass

	image = Image.objects.for_storage_path(storage_path)

	adjustment_class = get_adjustment_class(kwargs.pop('adjustment', DEFAULT_ADJUSTMENT))
	adjustment = adjustment_class.from_image(image, **kwargs)

	return HttpResponse(json.dumps(adjustment.info_dict()), mimetype="application/json")