import Image


DEFAULT_METHOD = 'fit'


methods = {}
calculations = {}


def runmethod(slug, im, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Runs the method registered as ``slug`` in the methods registry. All methods must accept ``width``, ``height``, ``max_width``, ``max_height``, and ``areas``, though they may ignore any of those parameters."""
	try:
		method = methods[slug]
	except KeyError:
		method = methods[DEFAULT_METHOD]
	
	return method(im, width=width, height=height, max_width=max_width, max_height=max_height, areas=areas)


def calculate_fit(im_w, im_h, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Calculates the dimensions of a :func:`fit` without actually resizing the image. Returns a tuple of the new width and height."""
	if height is None and width is None:
		return im_w, im_h
	
	im_r = float(im_w) / im_h
	
	if height is None:
		new_h = int(width / im_r)
		new_w = int(width)
	 	if max_height is not None and new_h > max_height:
			new_h = int(max_height)
			new_w = int(new_h * im_r)
	elif width is None:
		new_w = int(height * im_r)
		new_h = int(height)
		if max_width is not None and new_w > max_width:
			new_w = int(max_width)
			new_h = int(new_w / im_r)
	else:
		new_w = int(min(width, height * im_r))
		new_h = int(min(height, width / im_r))
	
	if new_w <= 0 or new_h <= 0:
		return im_w, im_h
	return new_w, new_h


def fit(im, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""
	Resizes ``im`` to fit completely inside the given dimensions without cropping or distortions. Returns a PIL Image instance.
	
	Rather than constraining an image to a specific width and height, width or height may be left as None, in which case the image can expand in the unspecified direction up to max_width or max_height, respectively.
	
	"""
	im_w, im_h = im.size
	
	new_w, new_h = calculate_fit(im_w, im_h, width, height, max_width, max_height, areas)
	
	if (new_w, new_h) == im.size:
		return im.copy()
	
	# Choose a method based on whether we're upscaling or downscaling.
	if new_w < im_w:
		method = Image.ANTIALIAS
	else:
		method = Image.BICUBIC
	
	return im.resize((new_w, new_h), method)
#methods.register(fit, verbose_name='Fit')
methods['fit'] = fit
calculations['fit'] = calculate_fit


def calculate_crop(im_w, im_h, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Calculates the dimensions of a :func:`crop` for the given parameters without actually cropping the image. Returns a tuple of the new width and height."""
	if width is None:
		if max_width is None:
			width = im_w
		else:
			width = min(im_w, max_width)
	if height is None:
		if max_height is None:
			height = im_h
		else:
			height = min(im_h, max_height)
	
	width = min(width, im_w)
	height = min(height, im_h)
	
	return width, height


def crop(im, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Crops an image to the given width and height. If any areas are passed in, they will be protected as appropriate in the crop. If ``width`` or ``height`` is not specified, the image may grow up to ``max_width`` or ``max_height`` respectively in the unspecified direction before being cropped."""
	im_w, im_h = im.size
	
	new_w, new_h = calculate_crop(im_w, im_h, width, height, max_width, max_height, areas)
	
	if not areas:
		x = (im_w - width) / 2
		y = (im_h - height) / 2
	else:
		coords = optimal_crop_dims(im, width, height, areas)
		x, y = coords[0]
	
	x2 = x + width
	y2 = y + height
	
	return im.crop((x, y, x2, y2))
#methods.register(crop, verbose_name='Crop')
methods['crop'] = crop
calculations['crop'] = calculate_crop


def calculate_fill(im_w, im_h, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Calculates the dimensions for a :func:`fill` without actually resizing the image. Returns a tuple of the new width and height."""
	# If there are no restrictions, just return the original dimensions.
	if height is None and width is None:
		return im_w, im_h
	
	im_r = float(im_w) / im_h
	
	if height is None:
		new_h = int(width / im_r)
		if max_height is not None:
			new_h = min(new_h, int(max_height))
		new_w = int(width)
	elif width is None:
		new_w = int(height * im_r)
		if max_width is not None:
			new_w = min(new_w, int(max_width))
		new_h = int(height)
	else:
		new_w = width
		new_h = height
	
	# Return the original dimensions for invalid input.
	if new_w <= 0 or new_h <= 0:
		return im_w, im_h
	return new_w, new_h


def fill(im, width=None, height=None, max_width=None, max_height=None, areas=None):
	"""Resizes an image so that the given dimensions are filled. If any areas are passed in, they will be protected in any necessary crops. If ``width`` or ``height`` is ``None``, then the unspecified dimension will be allowed to expand up to ``max_width`` or ``max_height``, respectively."""
	im_w, im_h = im.size
	
	new_w, new_h = calculate_fill(im_w, im_h, width, height, max_width, max_height, areas)
	
	if (new_w, new_h) == im.size:
		return im.copy()
	
	im_r = float(im_w) / im_h
	new_r = float(new_w) / new_h
	
	if new_r > im_r:
		# New ratio is wider. Cut the height.
		new_im = crop(im, im_w, int(im_w / new_r), areas=areas)
	else:
		new_im = crop(im, int(im_h * new_r), im_h, areas=areas)
	
	# After cropping the image to the right ratio, fit it to the new width and height.
	return fit(new_im, new_w, new_h)
#methods.register(fill, verbose_name='Fill')
methods['fill'] = fill
calculations['fill'] = calculate_fill


def optimal_crop_dims(im, width, height, areas):
	"Finds an optimal crop for a given image, width, height, and (protected) areas."
	min_penalty = None
	coords = None
	
	def get_penalty(area, x1, y1):
		x2 = x1 + width
		y2 = y1 + height
		if area.x1 >= x1 and area.x2 <= x2 and area.y1 >= y1 and area.y2 <= y2:
			# The area is enclosed.
			penalty_area = 0
		elif area.x2 < x1 or area.x1 > x2 or area.y2 < y1 or area.y1 > y2:
			penalty_area = area.area
		else:
			penalty_area = area.area - (min(area.x2 - x1, x2 - area.x1, area.width) * min(area.y2 - y1, y2 - area.y1, area.height))
		return penalty_area / area.priority
	
	for x in range(im.size[0] - width + 1):
		for y in range(im.size[1] - height + 1):
			penalty = 0
			for area in areas:
				penalty += get_penalty(area, x, y)
			
			if min_penalty is None or penalty < min_penalty:
				min_penalty = penalty
				coords = [(x, y)]
			elif penalty == min_penalty:
				coords.append((x, y))
	
	return coords


def convert_filetype(ftype):
"""Takes a file ending or mimetype and returns a valid mimetype or raises a ValueError."""
if '.' in ftype:
	try:
		return mimetypes.types_map[ftype]
	except KeyError:
		return mimetypes.common_types[ftype]
elif '/' in ftype:
	if ftype in mimetypes.types_map.values() or ftype in mimetypes.common_types.values():
		return ftype
	else:
		raise ValueError(_(u'Unknown MIME-type: %s' % ftype))
else:
	raise ValueError(_('Invalid MIME-type: %s' % ftype))
	

### Seam carving functions
"""
This uses Sameep Tandon's seam carving implementation.
https://github.com/sameeptandon/python-seam-carving/

This is extremely slow. Possible optimization would be to use
brain recall's CAIR: http://sites.google.com/site/brainrecall/cair
This is written in C++ and is much faster. It's unclear whether
cair can modify non-bmp files, though...
"""
try:
	from CAIS import *
except:
	pass
else:
	# It should be possible to add high-energy areas, but how? I would need to
	# track them throughout the resize process, I think.
	def seam_carve(im, width=None, height=None):
		im = im.copy()
		dimensions = get_resize_dimensions(im, width, height)
		
		if dimensions is None or dimensions == im.size:
			return im
		
		width, height = im.size
		x, y = dimensions
		
		while width > x:
			u = find_vertical_seam(gradient_filter(grayscale_filter(im)))
			im = delete_vertical_seam(im, u)
			width = im.size[0]
		
		while width < x:
			u = find_vertical_seam(gradient_filter(grayscale_filter(im)))
			im = add_vertical_seam(im, u)
			width = im.size[0]
		
		while height > y:
			u = find_horizontal_seam(gradient_filter(grayscale_filter(im)))
			im = delete_horizontal_seam(im, u)
			height = im.size[1]
		
		while height < y:
			u = find_horizontal_seam(gradient_filter(grayscale_filter(im)))
			im = add_horizontal_seam(im, u)
			height = im.size[1]
		
		return im

		import mimetypes
		from django.utils.translation import ugettext_lazy as _