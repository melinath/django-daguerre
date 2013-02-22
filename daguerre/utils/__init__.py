from hashlib import sha1

from django.core.files.base import File
from django.core.files.storage import default_storage
from django.core.files.temp import NamedTemporaryFile
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _
import mimetypes


#: Formats that we trust to be able to handle gracefully.
KEEP_FORMATS = ('PNG', 'JPEG', 'GIF')
#: Default format to convert other file types to.
DEFAULT_FORMAT = 'PNG'


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


def make_hash(*args, **kwargs):
	start = kwargs.get('start', None)
	stop = kwargs.get('stop', None)
	step = kwargs.get('step', None)
	return sha1(smart_str(u''.join([unicode(arg) for arg in args]))).hexdigest()[start:stop:step]


def save_image(image, storage_path, format=DEFAULT_FORMAT, storage=default_storage):
	"""
	Saves a PIL image file to the given storage_path using the given storage.
	Returns the final storage path of the saved file.

	"""
	if format not in KEEP_FORMATS:
		format = DEFAULT_FORMAT

	with NamedTemporaryFile() as temp:
		image.save(temp, format=format)
		return storage.save(storage_path, File(temp))
