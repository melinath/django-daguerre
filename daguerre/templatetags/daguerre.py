from __future__ import absolute_import

from django import template
from django.template.defaulttags import kwarg_re

from daguerre.utils.adjustments import AdjustmentHelper, BulkAdjustmentHelper


register = template.Library()


class AdjustmentNode(template.Node):
	def __init__(self, storage_path, kwargs, asvar=None):
		self.storage_path = storage_path
		self.kwargs = kwargs
		self.asvar = asvar

	def render(self, context):
		# storage_path might be an ImageFile.
		storage_path = self.storage_path.resolve(context)

		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())
		helper = AdjustmentHelper(storage_path, **kwargs)
		info_dict = helper.info_dict()

		if self.asvar is not None:
			context[self.asvar] = info_dict
			return ''
		return info_dict


class BulkAdjustmentNode(template.Node):
	def __init__(self, iterable, lookup, kwargs, asvar):
		self.iterable = iterable
		self.lookup = lookup
		self.kwargs = kwargs
		self.asvar = asvar

	def render(self, context):
		iterable = self.iterable.resolve(context)
		lookup = self.lookup.resolve(context)
		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())

		helper = BulkAdjustmentHelper(iterable, lookup, **kwargs)
		context[self.asvar] = helper.info_dicts()
		return ''


def _get_kwargs(parser, tag_name, bits):
	"""Helper function to get kwargs from a list of bits."""
	valid_kwargs = ('width', 'height', 'max_width', 'max_height', 'adjustment', 'crop')
	kwargs = {}
	
	for bit in bits:
		match = kwarg_re.match(bit)
		if not match:
			raise template.TemplateSyntaxError("Malformed arguments to `%s` tag" % tag_name)
		name, value = match.groups()
		if name not in valid_kwargs:
			raise template.TemplateSyntaxError("Invalid argument to `%s` tag: %s" % (tag_name, name))
		kwargs[str(name)] = parser.compile_filter(value)

	return kwargs


@register.tag
def adjust(parser, token):
	"""
	Returns a url to the adjusted image, or (with ``as``) stores a variable in the context containing an :class:`~AdjustmentInfoDict`.

	Syntax::
	
		{% adjust <image> [key=val key=val ...] [as <varname>] %}

	Where <image> is either an image file (like you would get as an ImageField's value) or a direct storage path for an image.

	If only one of width/height is supplied, the proportions are automatically constrained.
	Cropping and resizing will each only take place if the relevant variables are defined.

	The optional keyword arguments must be among:
	
	* width
	* height
	* max_width
	* max_height
	* adjustment
	* crop
	
	"""
	bits = token.split_contents()
	tag_name = bits[0]
	
	if len(bits) < 2:
		raise template.TemplateSyntaxError('"{0}" template tag requires at '
										   'least two arguments'.format(tag_name))

	image = parser.compile_filter(bits[1])
	bits = bits[2:]
	asvar = None
	
	if len(bits) > 1:
		if bits[-2] == 'as':
			asvar = bits[-1]
			bits = bits[:-2]
	
	return AdjustmentNode(image, _get_kwargs(parser, tag_name, bits), asvar=asvar)


@register.tag
def adjust_bulk(parser, token):
	"""
	Stores a variable in the context mapping instances from the iterable with adjusted images for those instances.

	Syntax:: 
	
		{% adjust_bulk <iterable> <lookup> [key=val key=val ...] as varname %}

	The keyword arguments have the same meaning as for :ttag:`{% adjust %}`.

	``lookup`` has the same format as a template variable (for example, ``"get_profile.image"``). The lookup will be performed on each item in the ``iterable`` to get the image which should be adjusted.

	"""
	bits = token.split_contents()
	tag_name = bits[0]
	
	if len(bits) < 5:
		raise template.TemplateSyntaxError('"{0}" template tag requires at '
										   'least five arguments'.format(tag_name))

	if bits[-2] != 'as':
		raise template.TemplateSyntaxError('The second to last argument to '
										   '{0} must be "as".'.format(tag_name))

	iterable = parser.compile_filter(bits[1])
	attribute = parser.compile_filter(bits[2])
	asvar = bits[-1]
	bits = bits[3:-2]

	kwargs = _get_kwargs(parser, tag_name, bits)
	if 'crop' in kwargs:
		raise template.TemplateSyntaxError('{% {0} %} does not currently support '
										   'cropping.'.format(tag_name))

	return BulkAdjustmentNode(iterable, attribute, kwargs, asvar)
