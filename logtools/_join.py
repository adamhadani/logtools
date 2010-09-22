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
logtools._join

Perform a join between log stream and
some other arbitrary source of data.
Can be used with pluggable drivers e.g
to join against database, other files etc.
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

__all__ = ['logjoin_parse_args', 'logjoin', 'logjoin_main']

def logjoin_parse_args():
    usage = "%prog " \
          "-f <field> " \
          "-d <delimiter_character> " \
          "-t <timestamp_format_string>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-p", "--part", dest="part", default=None, 
                    help="Part of URL to print out")

    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.part  = interpolate_config(options.part, options.profile, 'part')    

    return AttrDict(options.__dict__), args

def logjoin(fh, part, **kwargs):
    """Perform a join"""
    for line in imap(lambda x: x.strip(), fh):
        url = urlsplit(line)
        val = {
            "scheme": url.scheme,
            "domain": url.netloc,
            "netloc": url.netloc,
            "path":   url.path,
            "query":  parse_qs(url.query)
        }[part]
        yield val

def logjoin_main():
    """Console entry-point"""
    options, args = logjoin_parse_args()
    for row in logjoin(fh=sys.stdin, *args, **options):
        print >> sys.stdout, row

    return 0
