from __future__ import absolute_import

from django import template
from django.core.files.images import ImageFile
from django.template.defaulttags import kwarg_re

from daguerre.models import Image, AdjustedImage
from daguerre.utils.adjustments import AdjustmentHelper, AdjustmentInfoDict


register = template.Library()


class AdjustmentNode(template.Node):
	def __init__(self, storage_path, kwargs, asvar=None):
		self.storage_path = storage_path
		self.kwargs = kwargs
		self.asvar = asvar

	def render(self, context):
		storage_path = self.storage_path.resolve(context)

		if isinstance(storage_path, ImageFile):
			storage_path = storage_path.name

		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())
		helper = AdjustmentHelper(storage_path, **kwargs)
		info_dict = helper.info_dict()

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

	def _get_images(self, storage_paths, context):
		"""
		Fetches images from a cache in the current context.

		"""
		if self not in context.render_context:
			context.render_context[self] = {}
		image_cache = context.render_context[self]
		found = {}
		misses = set()
		for path in storage_paths:
			try:
				found[path] = image_cache[path]
			except KeyError:
				misses.add(path)

		# Try to fetch uncached images from the db.
		if misses:
			images = Image.objects.filter(storage_path__in=misses)
			for image in images:
				path = image.storage_path
				if path in image_cache:
					continue
				image_cache[path] = found[path] = image
				misses.discard(path)

		# Try to create any images still missing.
		if misses:
			for path in misses:
				try:
					image = Image.objects._create_for_storage_path(path)
				except IOError:
					pass
				else:
					image_cache[path] = found[path] = image
		return found

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

		kwargs = dict((k, v.resolve(context)) for k, v in self.kwargs.iteritems())

		# First try to fetch all previously-adjusted images.
		# The keys of items_dict are storage paths, and we don't want any
		# adjustments with requested crops for bulk! (Maybe later.)

		# Make a fake helper...
		helper = AdjustmentHelper('', **kwargs)
		helper._crop_area = None
		query_kwargs = helper.get_query_kwargs()
		del query_kwargs['storage_path']
		query_kwargs['storage_path__in'] = items_dict

		adjusted_images = AdjustedImage.objects.filter(**query_kwargs)
		for adjusted_image in adjusted_images:
			path = adjusted_image.storage_path
			if path not in items_dict:
				continue
			info_dict = adjusted_image.info_dict()
			for item in items_dict[path]:
				result_dict[item] = info_dict
			del items_dict[path]

		# Then get lazy info dicts for Images that already exist.
		if items_dict:
			images = Image.objects.filter(storage_path__in=items_dict)
			for image in images:
				path = image.storage_path
				if path not in items_dict:
					continue
				helper = AdjustmentHelper(image, **kwargs)
				info_dict = helper.info_dict(fetch_first=False)
				for item in items_dict[path]:
					result_dict[item] = info_dict
				del items_dict[path]

		# And finally make Images which didn't already exist.
		if items_dict:
			for path, items in items_dict.iteritems():
				helper = AdjustmentHelper(path, **kwargs)
				info_dict = helper.info_dict(fetch_first=False)
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
