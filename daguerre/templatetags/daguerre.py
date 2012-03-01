from __future__ import absolute_import

from django import template
from django.conf import settings
from django.template.defaulttags import kwarg_re

from daguerre.views import get_image_resize_info


register = template.Library()


class ImageProxy(object):
	"""This object handles the heavy lifting for the {% resize %} tag. Its unicode method renders the URL for the image, but it also provides access to the height and width of the resized image, calculated as if a resize were going to be undertaken without actually doing so."""
	def __init__(self, image, kwargs):
		self.image = image
		self.kwargs = kwargs
	
	def __unicode__(self):
		return self.url
	
	@property
	def url(self):
		if not hasattr(self, '_url'):
			self._setup()
		return self._url
	
	@property
	def width(self):
		if not hasattr(self, '_width'):
			self._setup()
		return self._width
	
	@property
	def height(self):
		if not hasattr(self, '_height'):
			self._setup()
		return self._height
	
	@property
	def ident(self):
		if not hasattr(self, '_ident'):
			self._setup()
		return self._ident
	
	def _setup(self):
		image = self.image
		kwargs = self.kwargs.copy()
		
		info = get_image_resize_info(image, **kwargs)
		
		self._width, self._height, self._url, self._ident = info['width'], info['height'], info['url'], info['ident']
	
	def __nonzero__(self):
		return self.url is not None


class ImageResizeNode(template.Node):
	def __init__(self, image, kwargs=None, asvar=None):
		self.image = image
		self.kwargs = kwargs
		self.asvar = asvar
	
	def render(self, context):
		image = self.image.resolve(context)
		kwargs = dict([(k, v.resolve(context)) for k, v in self.kwargs.items()])
		
		proxy = ImageProxy(image, kwargs)
		
		if self.asvar is not None:
			context[self.asvar] = proxy
			return ''
		return proxy


@register.tag
def resize(parser, token):
	"""
	Returns an instance of :class:`ImageProxy`, which can calculate the appropriate url for the resized version of an image, as well as knowing the actual resized width and height for the given parameters.
	
	Syntax::
	
		{% resize <image> [key=val key=val ...] [as <varname>] %}
	
	If only one of width/height is supplied, the proportions are automatically constrained.
	Cropping and resizing will each only take place if the relevant variables are defined.
	
	The optional keyword arguments must be among:
	
	* width
	* height
	* max_width
	* max_height
	* method
	* crop
	
	"""
	params = token.split_contents()
	
	if len(params) < 2:
		raise template.TemplateSyntaxError('"%s" template tag requires at least two arguments' % tag)
	
	tag = params[0]
	image = parser.compile_filter(params[1])
	params = params[2:]
	asvar = None
	
	if len(params) > 1:
		if params[-2] == 'as':
			asvar = params[-1]
			params = params[:-2]
	
	valid_kwargs = ('width', 'height', 'max_width', 'max_height', 'method', 'crop')
	kwargs = {}
	
	for param in params:
		match = kwarg_re.match(param)
		if not match:
			raise template.TemplateSyntaxError("Malformed arguments to `%s` tag" % tag)
		name, value = match.groups()
		if name not in valid_kwargs:
			raise template.TemplateSyntaxError("Invalid argument to `%s` tag: %s" % (tag, name))
		kwargs[str(name)] = parser.compile_filter(value)
	
	return ImageResizeNode(image, kwargs=kwargs, asvar=asvar)