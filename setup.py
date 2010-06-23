#!/usr/bin/env python
#
#  Licensed under the Apache License, Version 2.0 (the "License"); 
#  you may not use this file except in compliance with the License. 
#  You may obtain a copy of the License at 
#  
#      http://www.apache.org/licenses/LICENSE-2.0 
#     
#  Unless required by applicable law or agreed to in writing, software 
#  distributed under the License is distributed on an "AS IS" BASIS, 
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. 
#  See the License for the specific language governing permissions and 
#  limitations under the License. 

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
    url          = 'http://github.com/adamhadani/logtools',
    keywords     = ['logging', 'sampling', 'geoip', 'filter'],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",        
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Topic :: Internet :: Log Analysis",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Filters",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators"        
        ],
    long_description = """\
logtools
A log files analysis / filtering framework.

logtools encompasses of a few easy-to-use, easy to configure command-line
tools, typically used in conjunction with Apache logs.

The idea is to standardize log parsing and filtering using a coherent
configuration methodology and UNIX command-line interface (STDIN input streaming, command-line piping etc.)
so as to create a consistent environment for creating reports, charts and other such
log mining artifacts that are typically employed in a Website context.

Use case examples (Assuming a configured ~/.logtoolsrc, see Documentation):
* Get aggregated (IP, Country) count for all Bot visits:

  cat access_log.2010-05-15 | filterbots --print --reverse | geoip | sort | uniq -c | sort -k1,1nr

* Get a random sampling of 50 lines from an arbitrarily large input log stream:

  cat error_log.1 | filterbots --print | logsample -n50
""",
    
    packages = find_packages(),

    entry_points = {
        'console_scripts': [
            'filterbots = logtools:filterbots_main',
            'geoip = logtools:geoip_main',
            'logsample = logtools:logsample_main',
            'logplot = logtools:logplot_main',
        ]
    },

    zip_safe = True
)

