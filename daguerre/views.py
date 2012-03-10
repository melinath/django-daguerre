import mimetypes
import os
import Image as PILImage
from hashlib import sha1
import json

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, QueryDict
from django.shortcuts import get_object_or_404

from daguerre.cache import get_cache, set_cache
from daguerre.models import Image, AdjustedImage, Area
from daguerre.utils import runmethod, DEFAULT_METHOD, calculations


WIDTH = 'w'
HEIGHT = 'h'
MAX_WIDTH = 'max_w'
MAX_HEIGHT = 'max_h'
METHOD = 'm'
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


def get_image_resize_info(target, **kwargs):
	"""Returns a dictionary providing the ``ident``, ``url``, ``width``, and ``height`` of the image. The target should either be an Image instance or a file."""
	method = kwargs.pop('method', None)
	crop = kwargs.pop('crop', None)
	
	if isinstance(target, Image):
		adjusted_kwargs = {
			'requested_width': kwargs.get('width'),
			'requested_height': kwargs.get('height'),
			'requested_max_width': kwargs.get('max_width'),
			'requested_max_height': kwargs.get('max_height'),
			'requested_method': method or DEFAULT_METHOD
		}
		if crop is not None:
			adjusted_kwargs['requested_crop__name'] = crop
		try:
			adjusted = target.adjustedimage_set.get(**adjusted_kwargs)
		except AdjustedImage.DoesNotExist:
			ident = target.slug
			view = 'image_resize'
		else:
			return {
				'width': adjusted.width,
				'height': adjusted.height,
				'url': adjusted.adjusted.url,
				'ident': target.slug,
			}
	else:
		# the target is a file.
		ident = target.name
		
		if ident.startswith(settings.MEDIA_ROOT):
			# strip the media root prefix
			# TODO: See if there's a better way to check if the file is already in storage. This may break if we change storage backends, or if our MEDIA_ROOT is repeated in URLs for some reason
			# Maybe this isn't even the right place for this to go.
			media_root = settings.MEDIA_ROOT + '/' if settings.MEDIA_ROOT[-1] is not '/' else settings.MEDIA_ROOT
			ident = ident.replace(media_root,'')
			
		view = 'image_file_resize'
	
	
	try:
		width, height = target.width, target.height
	except AttributeError:
		# target is a file
		target = PILImage.open(target)
		width, height = target.size
	except:
		return {
			'width': None,
			'height': None,
			'url': None,
			'ident': None
		}
	
	calc = calculations[method or DEFAULT_METHOD]
	width, height = calc(width, height, **kwargs)
	
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
	if method is not None:
		qd[METHOD] = method
		kwargs['method'] = method
	qd[SECURITY] = make_security_hash(ident, *[kwargs.get(key) for key in ('width', 'height', 'max_width', 'max_height', 'method', 'crop')])
	
	url = "%s?%s" % (reverse(view, kwargs={'ident': ident}), qd.urlencode())
	
	return {
		'width': width,
		'height': height,
		'url': url,
		'ident': ident
	}


def image_view(func):
	"""Wraps a image-fetching function to create a view which caches its responses. TODO: This could probably use a touch of celery. Asynchronous image adjustment could be initiated when the template is rendered, rather than waiting until the page is loaded."""
	def inner(request, ident):
		width = clean_dim(request.GET.get(WIDTH, None))
		height = clean_dim(request.GET.get(HEIGHT, None))
		max_width = clean_dim(request.GET.get(MAX_WIDTH, None))
		max_height = clean_dim(request.GET.get(MAX_HEIGHT, None))
		crop = request.GET.get(CROP, None)
		method = request.GET.get(METHOD, None)
		security = request.GET.get(SECURITY, None)
		
		if not check_security_hash(security, ident, width, height, max_width, max_height, method, crop):
			raise Http404
		
		if method is None:
			method = DEFAULT_METHOD
		
		response = get_cache(ident, width, height, max_width, max_height, method, crop)
		
		if response is None:
			im = func(request, ident, width, height, max_width, max_height, method, crop)
			
			format = im.format or "png"
			mimetype = 'image/%s' % format.lower()
			ext = mimetypes.guess_extension(mimetype)
			response = HttpResponse(mimetype=mimetype)
			filename = os.path.splitext(os.path.basename(ident))[0]
			response['Content-Disposition'] = 'inline; filename=%s%s' % (filename, ext)
			
			if im.mode == 'CMYK':
				im = im.convert('RGB')
				format = 'JPEG'
			
			im.save(response, format)
			set_cache(ident, width, height, max_width, max_height, method, crop, response)
		
		return response
	return inner


@image_view
def adjusted_image(request, slug, width, height, max_width, max_height, method, crop):
	"""Gets or generates an :class:`AdjustedImage` based on an :class:`Image` with a :attr:`~Image.slug` of ``slug`` and returns the adjusted image."""
	kwargs = {
		'image__slug': slug,
		'requested_width': width,
		'requested_height': height,
		'requested_max_width': max_width,
		'requested_max_height': max_height,
		'requested_method': method,
	}
	
	if crop is not None:
		try:
			crop = Area.objects.get(image__slug=slug, name=crop)
		except Area.DoesNotExist:
			crop = None
		else:
			kwargs['requested_crop'] = crop
	
	try:
		image = AdjustedImage.objects.get(**kwargs)
	except AdjustedImage.DoesNotExist:
		try:
			base_image = Image.objects.get(slug=slug)
		except Image.DoesNotExist:
			raise Http404
		
		image = AdjustedImage.objects.adjust_image(base_image, width=width, height=height, max_width=max_width, max_height=max_height, method=method, crop=crop)
	
	# SB: This may raise an IOError or ValueError, but I don't remember what the cause is,
	# so don't catch for now.
	image.adjusted.open()
	return PILImage.open(image.adjusted)


def _ident_to_file(ident):
	path = default_storage.path(ident)
	
	try:
		im = PILImage.open(path)
	except IOError:
		raise Http404
	
	return im


@image_view
def resize_image_file(request, path, width, height, max_width, max_height, method, crop):
	"""Given an arbitrary path to a media file, returns a resized version of the file if it is an image and raises a 404 error otherwise."""
	im = _ident_to_file(path)
	
	# Resize image - always crop and scale this variant.
	return runmethod(method, im, width=width, height=height, max_width=max_width, max_height=max_height)


def ajax_resize_info(request, ident):
	if not request.is_ajax():
		raise Http404("Request is not AJAX.")
	
	width = clean_dim(request.GET.get(WIDTH, None))
	height = clean_dim(request.GET.get(HEIGHT, None))
	max_width = clean_dim(request.GET.get(MAX_WIDTH, None))
	max_height = clean_dim(request.GET.get(MAX_HEIGHT, None))
	
	if "/" in ident:
		# Then it's a path.
		target = _ident_to_file(ident)
	else:
		target = get_object_or_404(Image, slug=ident)
	
	kwargs = {
		'crop': request.GET.get('crop', None),
		'method': request.GET.get('method', None)
	}
	
	for k in ('width', 'height', 'max_width', 'max_height'):
		dim = clean_dim(request.GET.get(k))
		if dim is not None:
			kwargs[k] = dim
	
	info = get_image_resize_info(target, **kwargs)
	
	return HttpResponse(json.dumps(info), mimetype="application/json")