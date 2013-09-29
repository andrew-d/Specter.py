#!/usr/bin/env python

import os
import re
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


# Get the version (borrowed from SQLAlchemy)
our_dir = os.path.dirname(__file__)
fp = open(os.path.join(our_dir, 'specter', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(fp.read()).group(1)
fp.close()


packages = [
    'specter',
    'specter.tests',
]


# TODO: also requires PySide or PyQt, need to show that.
requirements = open('requirements.txt').readlines()
tests_requirements = requirements + open('test-requirements.txt').readlines()


setup(
    name='specter',
    version=VERSION,
    description='WebKit automation for Python',
    long_description=open('README.rst').read(),
    author='Andrew Dunham',
    author_email='andrew@du.nham.ca',
    url='',
    packages=packages,
    package_data={'': ['LICENSE'], 'specter': ['*.html', '*.js']},
    package_dir={'specter': 'specter'},
    include_package_data=True,
    install_requires=requirements,
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
    tests_require=tests_requirements,
)
