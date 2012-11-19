from django.test import TestCase

from daguerre.utils import make_security_hash


class SecurityHashTestCase(TestCase):
    def test_unicode(self):
        """
        Make sure that sha1 isn't choking on unicode characters.

        """
        hash_arg = u'banni\xe8re'
        make_security_hash(hash_arg)
