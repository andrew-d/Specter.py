#!/usr/bin/env python

import os
import sys

import specter


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


packages = [
    'specter',
    'specter.tests',
]


# TODO: also requires PySide or PyQt, need to show that.
requires = [
    'blinker',
]


setup(
    name='specter',
    version=specter.__version__,
    description='WebKit automation for Python',
    long_description=open('README.rst').read(),
    author='Andrew Dunham',
    author_email='andrew@du.nham.ca',
    url='',
    packages=packages,
    package_data={'': ['LICENSE'], 'specter': ['*.html', '*.js']},
    package_dir={'specter': 'specter'},
    include_package_data=True,
    install_requires=requires,
    license=open('LICENSE').read(),
    zip_safe=False,
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',

        # TODO
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.3',
    ),
)
