#!/usr/bin/env python

from setuptools import setup, find_packages

version = __import__('daguerre').VERSION

setup(
		name='daguerre',
		version='.'.join([str(v) for v in version]),
		description='Image management and processing for Djanog.',
		packages = find_packages(),
		install_requires = [
			'django-grappelli',
		],
		include_package_data = True
	)