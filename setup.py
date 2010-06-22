#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys
import os

setup(  
    name         = 'logtools',
    version      = '0.1',
    description  = 'Log analysis and filtering tools',
    author       = 'Adam Ever-Hadani',
    author_email = 'adamhadani@gmail.com',

    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'filterbots = logtools:filterbots',
            'geoip = logtools:geoip',
        ]
    },

    zip_safe = True
)

