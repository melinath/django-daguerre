from hashlib import sha1

from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _
import mimetypes


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
