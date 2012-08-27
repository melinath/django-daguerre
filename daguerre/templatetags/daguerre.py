from __future__ import absolute_import

from django import template
from django.conf import settings
from django.template.defaulttags import kwarg_re

from daguerre.models import Image
from daguerre.utils.adjustments import get_adjustment_class, DEFAULT_ADJUSTMENT


register = template.Library()


class AdjustmentNode(template.Node):
	def __init__(self, storage_path, kwargs=None, asvar=None):
		self.storage_path = storage_path
		self.kwargs = kwargs
		self.asvar = asvar
	
	def render(self, context):
		storage_path = self.storage_path.resolve(context)
		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())

		adjustment = None

		if isinstance(storage_path, basestring):
			try:
				image = Image.objects.for_storage_path(storage_path)
			except Image.DoesNotExist:
				pass
			else:
				adjustment_class = get_adjustment_class(kwargs.pop('adjustment', DEFAULT_ADJUSTMENT))
				try:
					adjustment = adjustment_class.from_image(image, **kwargs)
				except IOError:
					# IOError pops up if image.image doesn't reference
					# a present file.
					pass

		if adjustment is None:
			info_dict = {}
			url = ''
		else:
			info_dict = adjustment.info_dict()
			url = adjustment.url

		if self.asvar is not None:
			context[self.asvar] = info_dict
			return ''
		return url


@register.tag
def adjust(parser, token):
	"""
	Returns a url to the adjusted image, or (with ``as``) stores a variable in the context containing the results of :meth:`~Adjustment.info_dict`.

	Syntax::
	
		{% adjust <storage_path> [key=val key=val ...] [as <varname>] %}

	Where <storage_path> is the storage path for an image. This can be accessed as the ``name`` attribute of an ImageFieldFile.

	If only one of width/height is supplied, the proportions are automatically constrained.
	Cropping and resizing will each only take place if the relevant variables are defined.

	The optional keyword arguments must be among:
	
	* width
	* height
	* max_width
	* max_height
	* adjustment
	* crop

	.. seealso:: :class:`.AdjustedImageManager`
	
	"""
	params = token.split_contents()
	
	if len(params) < 2:
		raise template.TemplateSyntaxError('"%s" template tag requires at least two arguments' % tag)
	
	tag = params[0]
	storage_path = parser.compile_filter(params[1])
	params = params[2:]
	asvar = None
	
	if len(params) > 1:
		if params[-2] == 'as':
			asvar = params[-1]
			params = params[:-2]
	
	valid_kwargs = ('width', 'height', 'max_width', 'max_height', 'adjustment', 'crop')
	kwargs = {}
	
	for param in params:
		match = kwarg_re.match(param)
		if not match:
			raise template.TemplateSyntaxError("Malformed arguments to `%s` tag" % tag)
		name, value = match.groups()
		if name not in valid_kwargs:
			raise template.TemplateSyntaxError("Invalid argument to `%s` tag: %s" % (tag, name))
		kwargs[str(name)] = parser.compile_filter(value)
	
	return AdjustmentNode(storage_path, kwargs=kwargs, asvar=asvar)
