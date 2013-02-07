from __future__ import absolute_import

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.images import ImageFile
from django.template.defaulttags import kwarg_re

from daguerre.models import Image, AdjustedImage
from daguerre.utils import AdjustmentInfoDict
from daguerre.utils.adjustments import get_adjustment_class, DEFAULT_ADJUSTMENT


register = template.Library()


class BaseAdjustmentNode(template.Node):
	def _resolve_kwargs(self, kwargs, context):
		"""
		Given a key/var dictionary, resolves the variables and returns
		a tuple of the requested adjustment, a dictionary for making
		adjustments, and a dictionary for fetching :class:`AdjustedImage`
		instances.

		.. note::

			The dictionary for fetching :class:`AdjustedImage` instances
			will *not* include crop information, since that requires an
			:class:`Image` instance.

		"""
		kwargs = dict((k, v.resolve(context)) for k, v in kwargs.iteritems())

		query_kwargs = {
			'requested_adjustment': kwargs.pop('adjustment', DEFAULT_ADJUSTMENT)
		}
		for key in ('width', 'height', 'max_width', 'max_height'):
			value = kwargs.get(key)
			if value is None:
				query_kwargs['requested_{0}__isnull'.format(key)] = True
			else:
				query_kwargs['requested_{0}'.format(key)] = value

		return kwargs, query_kwargs

	def _get_images(self, storage_paths, context, create=True):
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
		if misses and create:
			for path in misses:
				try:
					image = Image.objects._create_for_storage_path(path)
				except IOError:
					pass
		return found

	def _get_image(self, storage_path, context):
		"""
		Fetches a single image from a cache in the current context.

		"""
		try:
			return self._get_images([storage_path], context)[storage_path]
		except KeyError:
			raise Image.DoesNotExist


class AdjustmentNode(BaseAdjustmentNode):
	def __init__(self, storage_path, kwargs, asvar=None):
		self.storage_path = storage_path
		self.kwargs = kwargs
		self.asvar = asvar
	
	def _complete(self, context, info_dict=None):
		if info_dict is None:
			info_dict = AdjustmentInfoDict()
		if self.asvar is not None:
			context[self.asvar] = info_dict
			return ''
		return info_dict

	def render(self, context):
		storage_path = self.storage_path.resolve(context)

		if isinstance(storage_path, ImageFile):
			storage_path = storage_path.name

		if not isinstance(storage_path, basestring):
			return self._complete(context)

		kwargs, query_kwargs = self._resolve_kwargs(self.kwargs, context)

		if 'crop' in kwargs:
			try:
				image = self._get_image(storage_path, context)
			except Image.DoesNotExist:
				return self._complete(context)
			try:
				area = image.areas.get(name=kwargs['crop'])
			except ObjectDoesNotExist:
				del kwargs['crop']
				query_kwargs['requested_crop__isnull'] = True
			else:
				query_kwargs['requested_crop'] = area

		# First try to fetch a previously-adjusted image.
		try:
			adjusted_image = AdjustedImage.objects.filter(image__storage_path=storage_path, **query_kwargs)[:1][0]
		except IndexError:
			pass
		else:
			return self._complete(context, adjusted_image.info_dict())

		# If there is no previously-adjusted image, set up a lazy
		# adjustment info dict.
		try:
			image = self._get_image(storage_path, context)
		except Image.DoesNotExist:
			return self._complete(context)

		adjustment_class = get_adjustment_class(query_kwargs['requested_adjustment'])
		try:
			adjustment = adjustment_class.from_image(image, **kwargs)
		except IOError:
			# IOError pops up if image.image doesn't reference
			# a present file.
			return self._complete(context)

		return self._complete(context, adjustment.info_dict())


class BulkAdjustmentNode(BaseAdjustmentNode):
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

		kwargs, query_kwargs = self._resolve_kwargs(self.kwargs, context)

		# First try to fetch all previously-adjusted images.
		# For now, this requires first fetching images with the storage path.
		images = self._get_images(items_dict, context, create=False).values()
		image_pk_dict = dict((image.pk, image) for image in images)
		adjusted_images = AdjustedImage.objects.filter(image_id__in=image_pk_dict, **query_kwargs)

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
		images = self._get_images(items_dict, context, create=True)

		for path, items in items_dict.iteritems():
			adjustment_class = get_adjustment_class(query_kwargs['requested_adjustment'])
			try:
				adjustment = adjustment_class.from_image(images[path], **kwargs)
			except (IOError, KeyError):
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
