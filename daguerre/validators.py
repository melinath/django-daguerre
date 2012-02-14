import mimetypes
import os

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from daguerre.utils import convert_filetype


class FileTypeValidator(object):
	"""
	This validator makes sure that a file's mimetype is in a certain list. The mimetype check uses
	the built-in mimetype library. TODO: it would be great to use python-magic, if it's available.
	"""
	def __init__(self, allowed=None, disallowed=None):
		self.disallowed = set([convert_filetype(ftype) for ftype in disallowed or []])
		self.allowed = set([convert_filetype(ftype) for ftype in allowed or []]) - self.disallowed
	
	def __call__(self, value):
		mimetype, encoding = mimetypes.guess_type(value.name, strict=False)
		
		if mimetype is None:
			raise ValidationError(_(u'Unknown file type: %s' % os.path.splitext(value.name)[1]))
		
		if self.allowed and mimetype not in self.allowed:
			raise ValidationError(_(u"Only the following mime types may be uploaded: %s" % ', '.join(self.allowed)))
		if self.disallowed and mimetype not in self.disallowed:
			raise ValidationError(_(u"The following mime types may not be uploaded: %s" % ', '.join(self.disallowed)))