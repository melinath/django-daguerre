from django.test import TestCase

from daguerre.utils import make_hash


class MakeHashTestCase(TestCase):
    def test_unicode(self):
        """
        Make sure that sha1 isn't choking on unicode characters.

        """
        hash_arg = u'banni\xe8re'
        make_hash(hash_arg)
