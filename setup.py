#!/usr/bin/env python

import os
from setuptools import setup, find_packages

version = __import__('daguerre').__version__

setup(
    name='django-daguerre',
    version='.'.join([str(v) for v in version]),
    url="http://django-daguerre.readthedocs.org/",
    description='Image management and processing for Django.',
    long_description=open(
            os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Pillow>=2.0',
        'django>=1.4.5',
        'six>=1.3.0',
    ],
    extras_require={
        'docs': ["sphinx>=1.0"],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Multimedia :: Graphics',
        'Framework :: Django',
    ],
)
