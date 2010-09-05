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
logtools._merge
Logfile merging utilities.
These typically help in streaming multiple 
individually sorted input logfiles through, outputting them in
combined sorted order (typically by date field)
"""
import os
import re
import sys
import logging
from itertools import imap
from datetime import datetime
from optparse import OptionParser
from heapq import heappush, heappop, merge

from _config import logtools_config, interpolate_config, AttrDict
import logtools.parsers

__all__ = ['logmerge_parse_args', 'logmerge', 'logmerge_main']


def logmerge_parse_args():
    usage = "%prog -f <field> -d <delimiter> filename1 filename2 ..."
    parser = OptionParser(usage=usage)
    
    parser.add_option("-f", "--field", dest="field", default=None,
                    help="Field index to use as key for sorting by (1-based)")
    parser.add_option("-d", "--delimiter", dest="delimiter", default=None, 
                    help="Delimiter character for fields in logfile")
    parser.add_option("-n", "--numeric", dest="numeric", default=None, action="store_true",
                    help="Parse key field value as numeric and sort accordingly")
    parser.add_option("-t", "--datetime", dest="datetime", default=None, action="store_true",
                    help="Parse key field value as a date/time timestamp and sort accordingly")
    parser.add_option("-F", "--dateformat", dest="dateformat",
                      help="Format string for parsing date-time field (used with --datetime)")        
    parser.add_option("-p", "--parser", dest="parser", default=None, 
                    help="Log format parser (e.g 'CommonLogFormat'). See documentation for available parsers.")
    
    parser.add_option("-P", "--profile", dest="profile", default='logmerge',
                      help="Configuration profile (section in configuration file)")
    
    options, args = parser.parse_args()
    
    # Interpolate from configuration
    options.field = interpolate_config(options.field, 
                                    options.profile, 'field')
    options.delimiter = interpolate_config(options.delimiter, 
                                    options.profile, 'delimiter', default=' ')
    options.numeric = interpolate_config(options.numeric, options.profile, 
                                    'numeric', default=False, type=bool) 
    options.datetime = interpolate_config(options.datetime, options.profile, 
                                    'datetime', default=False, type=bool)     
    options.dateformat = interpolate_config(options.dateformat, 
                                    options.profile, 'dateformat', default=False)    
    options.parser = interpolate_config(options.parser, 
                                    options.profile, 'parser', default=False)    

    return AttrDict(options.__dict__), args

def logmerge(options, args):
    """Perform merge on multiple input logfiles
    and emit in sorted order using a priority queue"""
    
    delimiter = options.delimiter
    field = options.field

    key_func = None
    if options.get('parser', None):
        # Use a parser to extract field to merge/sort by
        parser = eval(options.parser, vars(logtools.parsers), {})()
        if field.isdigit():            
            extract_func = lambda x: parser(x.strip()).by_index(int(field)-1)
        else:
            extract_func = lambda x: parser(x.strip())[field]
    else:
        # No parser given, use indexed field based extraction
        extract_func = lambda x: x.strip().split(delimiter)[int(field)-1]
        
    if options.get('numeric', None):
        key_func = lambda x: (int(extract_func(x)), x)
    elif options.get('datetime', None):
        key_func = lambda x: (datetime.strptime(extract_func(x), \
                                    options.dateformat), x)            
    else:
        key_func = lambda x: (extract_func(x), x)
        
    iters = (imap(key_func, open(filename, "r")) for filename in args)
    
    for k, line in merge(*iters):
        yield k, line.strip()
    
def logmerge_main():
    """Console entry-point"""
    options, args = logmerge_parse_args()
    for key, line in logmerge(options, args):
        print line
    return 0
