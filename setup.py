#!/usr/bin/env python

import os

d = dict(name='txdlo',
         version='0.0.3',
         provides=['txdlo'],
         maintainer='Terry Jones',
         maintainer_email='terry@jon.es',
         url='https://github.com/terrycojones/txdlo',
         download_url='https://github.com/terrycojones/txdlo',
         packages=['txdlo', 'txdlo.test'],
         keywords=['twisted deferred observer'],
         classifiers=[
             'Programming Language :: Python',
             'Framework :: Twisted',
             'Development Status :: 4 - Beta',
             'Intended Audience :: Developers',
             'License :: OSI Approved :: Apache Software License',
             'Operating System :: OS Independent',
             'Topic :: Software Development :: Libraries :: Python Modules',
         ],
         description=('A Twisted class for observing a collection of deferreds.'))

try:
    from setuptools import setup
    _ = setup  # Keeps pyflakes from complaining.
except ImportError:
    from distutils.core import setup
else:
    d['install_requires'] = ['Twisted']

setup(**d)
