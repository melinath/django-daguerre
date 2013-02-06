from __future__ import absolute_import

from django import template
from django.core.files.images import ImageFile
from django.template.defaulttags import kwarg_re

from daguerre.models import Image, AdjustedImage
from daguerre.utils import AdjustmentInfoDict
from daguerre.utils.adjustments import get_adjustment_class, DEFAULT_ADJUSTMENT


register = template.Library()


class AdjustmentNode(template.Node):
	def __init__(self, image, kwargs, asvar=None):
		self.image = image
		self.kwargs = kwargs
		self.asvar = asvar
	
	def render(self, context):
		image = self.image.resolve(context)

		if isinstance(image, ImageFile):
			storage_path = image.name
		else:
			storage_path = image

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
			info_dict = AdjustmentInfoDict()
		else:
			info_dict = adjustment.info_dict()

		if self.asvar is not None:
			context[self.asvar] = info_dict
			return ''
		return info_dict


class BulkAdjustmentNode(template.Node):
	def __init__(self, iterable, attribute, kwargs, asvar):
		self.iterable = iterable
		self.attribute = attribute
		self.kwargs = kwargs
		self.asvar = asvar

	def render(self, context):
		iterable = self.iterable.resolve(context)
		attribute = self.attribute.resolve(context)

		result_dict = {}

		items_dict = {}
		for item in iterable:
			path = getattr(item, attribute, None)
			if isinstance(path, ImageFile):
				path = path.name
			if isinstance(path, basestring):
				items_dict.setdefault(path, []).append(item)
			else:
				result_dict[item] = AdjustmentInfoDict()

		images = Image.objects.filter(storage_path__in=items_dict)
		image_pk_dict = dict((image.pk, image) for image in images)
		image_path_dict = dict((image.storage_path, image) for image in images)

		# kwargs is used for any adjustments; query_kwargs is used to find
		# old already-created adjustments.
		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())
		requested_adjustment = kwargs.pop('adjustment', DEFAULT_ADJUSTMENT)

		query_kwargs = {
			'requested_adjustment': requested_adjustment
		}
		for key in ('width', 'height', 'max_width', 'max_height'):
			value = kwargs.get(key)
			if value is None:
				query_kwargs['requested_{0}__isnull'.format(key)] = True
			else:
				query_kwargs['requested_{0}'.format(key)] = value

		adjusted_images = AdjustedImage.objects.filter(image_id__in=image_pk_dict,
													   **query_kwargs)
		# First assign all the values that have been previously adjusted.
		for adjusted_image in adjusted_images:
			if adjusted_image.image_id not in image_pk_dict:
				continue
			image = image_pk_dict[adjusted_image.image_id]
			if image.storage_path not in items_dict:
				continue
			info_dict = adjusted_image.info_dict()
			for item in items_dict[image.storage_path]:
				result_dict[item] = info_dict
			del image_pk_dict[adjusted_image.image_id]
			del items_dict[image.storage_path]

		# Then make sure each remaining item has an associated image,
		# and assign it.
		for path, items in items_dict.iteritems():
			if path in image_path_dict:
				image = image_path_dict[path]
			else:
				try:
					image = Image.objects.for_storage_path(path)
				except Image.DoesNotExist:
					image = None
			adjustment = None
			if image is not None:
				adjustment_class = get_adjustment_class(requested_adjustment)
				try:
					adjustment = adjustment_class.from_image(image, **kwargs)
				except IOError:
					pass
			if adjustment is None:
				info_dict = AdjustmentInfoDict()
			else:
				info_dict = adjustment.info_dict()
			for item in items:
				result_dict[item] = info_dict

		context[self.asvar] = result_dict
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
	Returns a url to the adjusted image, or (with ``as``) stores a variable in the context containing the results of :meth:`~Adjustment.info_dict`.

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

	.. seealso:: :class:`.AdjustedImageManager`
	
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
	{% adjust_bulk <iterable> <attribute> [key=val key=val ...] as varname %}
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
