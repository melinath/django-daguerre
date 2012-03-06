import mimetypes
import os
import Image as PILImage
from hashlib import sha1
import json

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, QueryDict, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from daguerre.middleware import private_ajax
from daguerre.models import Image, AdjustedImage, Area
from daguerre.utils import get_adjustment, DEFAULT_ADJUSTMENT


WIDTH = 'w'
HEIGHT = 'h'
MAX_WIDTH = 'max_w'
MAX_HEIGHT = 'max_h'
ADJUSTMENT = 'a'
SECURITY = 's'
CROP = 'c'


def clean_dim(dim):
	if dim is not None:
		try:
			dim = int(dim)
		except ValueError:
			raise Http404
	return dim


def make_security_hash(*args):
	return sha1(''.join([unicode(arg) for arg in args]) + settings.SECRET_KEY).hexdigest()[::2]


def check_security_hash(sec_hash, *args):
	return sec_hash == make_security_hash(*args)


def get_image_resize_info(image, **kwargs):
	"""Returns a dictionary providing the ``ident``, ``url``, ``width``, and ``height`` of the image. The image should be an Image instance."""
	adjustment = kwargs.pop('adjustment', DEFAULT_ADJUSTMENT)
	crop = kwargs.pop('crop', None)
	
	adjusted_kwargs = {
		'requested_width': kwargs.get('width'),
		'requested_height': kwargs.get('height'),
		'requested_max_width': kwargs.get('max_width'),
		'requested_max_height': kwargs.get('max_height'),
		'requested_adjustment': adjustment
	}
	if crop is not None:
		adjusted_kwargs['requested_crop__name'] = crop

	storage_path = image.image.name
	try:
		adjusted = image.adjustedimage_set.get(**adjusted_kwargs)
	except AdjustedImage.DoesNotExist:
		pass
	else:
		return {
			'width': adjusted.width,
			'height': adjusted.height,
			'url': adjusted.adjusted.url,
			'ident': storage_path
		}
	
	try:
		width, height = image.width, image.height
	except Exception:
		return {
			'width': None,
			'height': None,
			'url': None,
			'ident': None
		}

	image.image.open('r')
	adjustment = get_adjustment(adjustment, PILImage.open(image.image), **kwargs)
	width, height = adjustment.calculate()
	
	qd = QueryDict('', mutable=True)
	if 'width' in kwargs:
		qd[WIDTH] = kwargs['width']
	if 'height' in kwargs:
		qd[HEIGHT] = kwargs['height']
	if 'max_width' in kwargs:
		qd[MAX_WIDTH] = kwargs['max_width']
	if 'max_height' in kwargs:
		qd[MAX_HEIGHT] = kwargs['max_height']
	if crop is not None:
		qd[CROP] = crop
		kwargs['crop'] = crop
	qd[ADJUSTMENT] = adjustment
	kwargs['adjustment'] = adjustment
	qd[SECURITY] = make_security_hash(storage_path, *[kwargs.get(key) for key in ('width', 'height', 'max_width', 'max_height', 'adjustment', 'crop')])
	
	url = "%s?%s" % (reverse('daguerre_adjusted_image_redirect', kwargs={'storage_path': storage_path}), qd.urlencode())
	
	return {
		'width': width,
		'height': height,
		'url': url,
		'ident': storage_path
	}


def adjusted_image_redirect(request, storage_path):
	"""
	Returns a redirect to an :attr:`~AdjustedImage.adjusted` file, first creating the :class:`~AdjustedImage` if necessary.

	:param storage_path: The path to the original image file, relative to the default storage.

	"""
	width = clean_dim(request.GET.get(WIDTH, None))
	height = clean_dim(request.GET.get(HEIGHT, None))
	max_width = clean_dim(request.GET.get(MAX_WIDTH, None))
	max_height = clean_dim(request.GET.get(MAX_HEIGHT, None))
	crop = request.GET.get(CROP, None)
	adjustment = request.GET.get(ADJUSTMENT, DEFAULT_ADJUSTMENT)
	security = request.GET.get(SECURITY, None)

	if not check_security_hash(security, storage_path, width, height, max_width, max_height, adjustment, crop):
		raise Http404

	image = Image.objects.for_storage_path(storage_path)

	if crop is not None:
		try:
			crop = Area.objects.get(image__slug=slug, name=crop)
		except Area.DoesNotExist:
			crop = None

	# Once you have the Image, adjust it!
	adjusted = AdjustedImage.objects.adjust_image(image, width=width, height=height, max_width=max_width, max_height=max_height, adjustment=adjustment, crop=crop)

	return HttpResponseRedirect(adjusted.adjusted.url)


@private_ajax
def ajax_adjustment_info(request, storage_path):
	if not request.is_ajax():
		raise Http404("Request is not AJAX.")
	
	width = clean_dim(request.GET.get(WIDTH, None))
	height = clean_dim(request.GET.get(HEIGHT, None))
	max_width = clean_dim(request.GET.get(MAX_WIDTH, None))
	max_height = clean_dim(request.GET.get(MAX_HEIGHT, None))

	image = Image.objects.for_storage_path(storage_path)
	
	kwargs = {
		'crop': request.GET.get('crop', None),
		'adjustment': request.GET.get('adjustment', DEFAULT_ADJUSTMENT)
	}
	
	for k in ('width', 'height', 'max_width', 'max_height'):
		dim = clean_dim(request.GET.get(k))
		if dim is not None:
			kwargs[k] = dim
	
	info = get_image_resize_info(image, **kwargs)
	
	return HttpResponse(json.dumps(info), mimetype="application/json")