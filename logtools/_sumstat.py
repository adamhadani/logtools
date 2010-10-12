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
"""
logtools._sumstat

Generates summary statistics
for a given logfile of the form:

<count> <value>

logfile is expected to be sorted (decreasing) by count
"""
import re
import sys
import logging

from time import time
from itertools import imap
from datetime import datetime
from optparse import OptionParser
from urlparse import parse_qs, urlsplit

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['sumstat_parse_args', 'sumstat', 'sumstat_main']

def sumstat_parse_args():
    usage = "%prog -p <url_part>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")    

    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()
    
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter')

    return AttrDict(options.__dict__), args


def sumstat(fh, delimiter, **kwargs):
    counts = []
    for line in imap(lambda x: x.strip(), fh):
        count, val = line.split(delimiter)
        count = int(count)
        counts.append(count)


def sumstat_main():
    """Console entry-point"""
    options, args = urlparse_parse_args()
    sumstat(fh=sys.stdin, *args, **options)
    return 0
