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

setup(
    name         = 'logtools',
    version      = '0.8.7p3',
    description  = 'Log analysis and filtering tools',
    author       = 'Adam Ever-Hadani, additions Alain Lich',
    author_email = '',
    url          = 'http://github.com/AlainLich/logtools',
    keywords     = ['logging', 'sampling', 'geoip', 'filterbots', 'aggregate',
                    'logparse', 'logmerge', 'logjoin', 'urlparse', 'logplot',
                    'logdb', 'qps', 'filter'],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8.6",
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
A log files analysis / filtering framework.

logtools encompasses of a few easy-to-use, easy to configure command-line
tools, typically used in conjunction with Apache logs, and other common formats.

The idea is to standardize log parsing and filtering using a coherent
configuration methodology and UNIX command-line interface (STDIN input streaming, command-line piping etc.)
so as to create a consistent environment for creating reports, charts and other such
log mining artifacts that are typically employed in a Website context.

This software is distributed under the Apache 2.0 license.
""",

    packages = find_packages(),

    scripts = ['scripts/aggregate', 'scripts/colsum',
                'scripts/percentiles', 'scripts/triggered-regexp'],

    include_package_data = False,

    install_requires = [
        "greenlet>=1.0.0",
        "lark-parser==0.6.7",  # ran into issue on Github,
                               # lark-parser 0.11.2 is installed but lark-parser==0.6.* is required by
                               # {'syslog-rfc5424-parser'}
        "numpy>=1.20.1",
        "pandas>=1.2.3",
        "prettytable>=2.1.0",
        "python-dateutil>=2.8.1",
        "pytz>=2021.1",
        "SQLAlchemy>=1.4.13",   # looking for compatibility with MySQL8.0
        "syslog-rfc5424-parser>=0.3.2",
        "wcwidth>=0.2.5"
    ],

    entry_points = {
        'console_scripts': [
            'filterbots = logtools:filterbots_main',
            'flattenjson = logtools:flattenjson_main',
            'geoip = logtools:geoip_main',
            'logparse = logtools:logparse_main',
            'logmerge = logtools:logmerge_main',
            'logjoin = logtools:logjoin_main',
            'logdb = logtools:logdb_main',
            'logplot = logtools:logplot_main',
            'logsample = logtools:logsample_main',
            'logfilter = logtools:logfilter_main',
            'logtail = logtools:logtail_main',
            'qps = logtools:qps_main',
            'sumstat = logtools:sumstat_main',
            'urlparse = logtools:urlparse_main',
        ]
    },

    tests_require = ['nose>=0.11', "coverage>=3.4"],

    test_suite = "nose.collector",

    zip_safe = True
)

