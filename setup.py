#!/usr/bin/env python

import os
from setuptools import setup, find_packages

version = __import__('daguerre').VERSION

setup(
		name='django-daguerre',
		version='.'.join([str(v) for v in version]),
		url="http://django-daguerre.readthedocs.org/",
		description='Image management and processing for Django.',
		long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
		license='BSD',
		packages=find_packages(),
		include_package_data=True,
		zip_safe=False,
		install_requires=[
			'PIL',
		],
		extras_require={
			'docs': ["sphinx>=1.0"],
		},
		classifiers=[
			'Development Status :: 4 - Beta',
			'Environment :: Web Environment',
			'Intended Audience :: Developers',
			'License :: OSI Approved :: BSD License',
			'Operating System :: OS Independent',
			'Programming Language :: Python',
			'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
			'Topic :: Multimedia :: Graphics',
			'Framework :: Django',
		],
	)