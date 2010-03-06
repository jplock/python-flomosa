#!/usr/bin/env python
#from distutils.core import setup
from setuptools import setup, find_packages

setup(name='flomosa',
      version='0.0.1',
      description="Library for interfacing with Flomosa's API",
      author='Justin Plock',
      author_email='justin@flomosa.com',
      url='http://github.com/flomosa/python-flomosa',
      packages=find_packages(),
      license='MIT License',
      install_requires=['httplib2>=0.6.0', 'oauth2>=1.0.6', 'simplejson>=2.0.9'],
      keywords='flomosa',
      zip_safe=True,
      tests_require=['nose', 'coverage'])