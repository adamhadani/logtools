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
logtools._parse
Log format parsing programmatic and command-line utilities.
uses the logtools.parsers module
"""
import os
import re
import sys
import logging
from itertools import imap
from functools import partial
from operator import and_
from optparse import OptionParser

import logtools.parsers
from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['logparse_parse_args', 'logparse', 'logparse_main']


def multikey_getter_gen(parser, keys, is_indices=False, delimiter="\t"):
    """Generator meta-function to return a function
    parsing a logline and returning multiple keys (tab-delimited)"""
    if is_indices:
        keys = map(int, keys)
    elif not hasattr(keys, 'intersection'):
        keys = set(keys)
        
    def multikey_getter(line, parser, keyset):
        data = parser(line.strip())
        return delimiter.join((data[k] for k in keyset))
    
    def multiindex_getter(line, parser, keyset):
        data = parser(line.strip())
        return delimiter.join((data.by_index(idx-1, raw=True) for idx in keys))

    if is_indices is True:
        # Field indices
        return partial(multiindex_getter, parser=parser, keyset=keys)
    else:
        # Field names
        return partial(multikey_getter, parser=parser, keyset=keys)


def logparse_parse_args():
    parser = OptionParser()
    parser.add_option("-p", "--parser", dest="parser", default=None, 
                    help="Log format parser (e.g 'CommonLogFormat'). See documentation for available parsers.")
    parser.add_option("-F", "--format", dest="format", default=None, 
                    help="Format string. Used by the parser (e.g AccessLog format specifier)")    
    parser.add_option("-f", "--field", dest="field", default=None,
                    help="Parsed Field index to output")    
    parser.add_option("-i", "--ignore", dest="ignore", default=None, action="store_true",
                    help="Ignore missing fields errors (skip lines with missing fields)")    
    
    parser.add_option("-P", "--profile", dest="profile", default='logparse',
                      help="Configuration profile (section in configuration file)")
    
    options, args = parser.parse_args()
    
    # Interpolate from configuration
    options.parser = interpolate_config(options.parser, options.profile, 'parser') 
    options.format = interpolate_config(options.format, options.profile, 'format', 
                                        default=False) 
    options.field = interpolate_config(options.field, options.profile, 'field')
    options.ignore = interpolate_config(options.ignore, options.profile, 'ignore', 
                                        default=False, type=bool)
    

    return AttrDict(options.__dict__), args

def logparse(options, args, fh):
    """Parse given input stream using given
    parser class and emit specified field(s)"""

    field = options.field
    
    parser = eval(options.parser, vars(logtools.parsers), {})()
    if options.get('format', None):
        parser.set_format(options.format)
        
    keyfunc = None
    if isinstance(options.field, int) or \
       (isinstance(options.field, basestring) and options.field.isdigit()):
        # Field given as integer (index)
        field = int(options.field) - 1            
        key_func = lambda x: parser(x.strip()).by_index(field, raw=True)
    else:
        # Field given as string
        
        # Check how many fields are requested        
        keys = options.field.split(",")
        L = len(keys)
        if L == 1:
            key_func = lambda x: parser(x.strip())[field]
        else:
            # Multiple fields requested
            is_indices = reduce(and_, (k.isdigit() for k in keys), True)
            key_func = multikey_getter_gen(parser, keys, is_indices=is_indices)
    
    for line in fh:
        try:
            yield key_func(line)
        except KeyError:
            if options.ignore:
                logging.debug("Could not match fields for parsed line: %s", line)
                continue
            else:
                raise
    
def logparse_main():
    """Console entry-point"""
    options, args = logparse_parse_args()
    for row in logparse(options, args, fh=sys.stdin.readlines()):
        print row
    return 0
