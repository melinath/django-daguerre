from hashlib import sha1

from django.conf import settings
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


def make_security_hash(*args):
	return sha1(''.join([unicode(arg) for arg in args]) + settings.SECRET_KEY).hexdigest()[::2]


def check_security_hash(sec_hash, *args):
	return sec_hash == make_security_hash(*args)

class AdjustmentInfoDict(dict):
	"A simple dict subclass for making image data more usable in templates."
	
	def __unicode__(self):
		return self.get('url', u'')