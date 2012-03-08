import doctest
from daguerre import utils
from django.utils import unittest

def suite():
	suite = unittest.TestSuite()
	# register some doctests
	suite.addTest(doctest.DocTestSuite(utils))
	return suite