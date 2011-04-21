#!/usr/bin/env python
#-*- coding:utf-8 -*-

from distutils.core import setup

setup(
    name = 'mobilise',
    description = 'Group of helper function to deploy and run Django projects',
    version = '0.0.1',
    author = 'Simon Luijk',
    author_email = 'simon@luijk.co.uk',
    url = 'http://www.apricotwebsolutions.com/',
    packages = ['mobilise',],
    entry_points="""
        [console_scripts]
        mob=mobilise.mob:main
        dj-daemon=mobilise.dj_daemon:main
    """,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
