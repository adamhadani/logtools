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
logtools._urlparse

Parses URLs, Decodes query parameters,
and allows some selection on URL parts.
"""
import re
import sys
import logging
from time import time
from itertools import imap
from datetime import datetime
from urllib import unquote_plus
from optparse import OptionParser
from urlparse import parse_qs, urlsplit

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['urlparse_parse_args', 'urlparse', 'urlparse_main']

def urlparse_parse_args():
    usage = "%prog -p <url_part>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-p", "--part", dest="part", default=None, 
                    help="Part of URL to print out. Valid values: scheme, domain, netloc, path, query")
    parser.add_option("-q", "--query-params", dest="query_params", default=None,
                      help="Query parameters to print. Used in conjunction with '-p query'. Can specify multiple ones seperated by comma")
    parser.add_option("-d", "--decode", dest="decode", action="store_true",
                      help="Decode mode - Unquote input text, translating %xx characters and '+' into spaces")

    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    if not options.decode and not options.part:
        parser.error("Must supply -p (part) when not working in decode (-d) mode. See --help for usage instructions.")
        
    # Interpolate from configuration and open filehandle
    options.part  = interpolate_config(options.part, options.profile, 'part', default=False)    
    options.query_params = interpolate_config(options.query_params, options.profile, 'query_params', default=False)  
    options.decode = interpolate_config(options.decode, options.profile, 'decode', default=False) 

    return AttrDict(options.__dict__), args

def urlparse(fh, part=None, query_params=None, decode=False, **kwargs):
    """URLParse"""
    
    _yield_func = lambda x: x
    if query_params and part == 'query':
        if query_params.find(',') == -1:
            _yield_func = lambda x: val.get(query_params, (None,))[0]
        else:
            # Multiple query params specified on command line
            query_params = query_params.split(",")
            _yield_func = lambda x: \
                    [val.get(p, (None,))[0] for p in query_params]
    
    if decode is True:
        for line in imap(lambda x: x.strip(), fh):
            yield unquote_plus(line)
    else:
        for line in imap(lambda x: x.strip(), fh):
            url = urlsplit(line)
            val = {
                "scheme": url.scheme,
                "domain": url.netloc,
                "netloc": url.netloc,
                "path":   url.path,
                "query":  parse_qs(url.query)
            }[part]
            
            yield _yield_func(val)


def urlparse_main():
    """Console entry-point"""
    options, args = urlparse_parse_args()
    for parsed_url in urlparse(fh=sys.stdin, *args, **options):
        if parsed_url:
            if hasattr(parsed_url, '__iter__'):
                # Format as tab-delimited for output
                parsed_url = "\t".join(parsed_url)
            print parsed_url
        else:
            # Lines where we couldnt get any match (e.g when using -q)
            print ''

    return 0
