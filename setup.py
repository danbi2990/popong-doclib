#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='popong_doclib',
      version='0.2.1',
      description='Team POPONG Document processing Library',
      url='http://bitbucket.org/teampopong/popong-doclib',
      author='Team POPONG',
      author_email='contact@popong.com',
      license='Apache 2.0',
      packages=['popong_doclib', 'popong_doclib.meeting', 'popong_doclib.bill', 'popong_doclib.utils'],
      zip_safe=False)
