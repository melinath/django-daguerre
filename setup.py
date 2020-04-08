#!/usr/bin/env python

import os
from setuptools import setup, find_packages

version = __import__('daguerre').__version__

setup(
    name='django-daguerre',
    version='.'.join([str(v) for v in version]),
    url="http://django-daguerre.readthedocs.org/",
    maintainer='Stephen Burrows',
    maintainer_email='stephen.r.burrows@gmail.com',
    description='On-the-fly image manipulation for Django 1.11+.',
    long_description=open(
            os.path.join(os.path.dirname(__file__), 'README.rst')
    ).read(),
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Pillow',
        'django>=1.11',
    ],
    extras_require={
        'docs': ["sphinx-rtd-theme>=0.1.5"],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Multimedia :: Graphics',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
    ],
)
