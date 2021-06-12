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
#
# ........................................ NOTICE
#
# This file has been derived and modified from a source licensed under Apache Version 2.0.
# See files NOTICE and README.md for more details.
#
# ........................................ ******

"""
logtools._parse
Log format parsing programmatic and command-line utilities.
uses the logtools.parsers module
"""
import sys
import logging
from operator import and_
from optparse import OptionParser
from functools import reduce
import json

import logtools.parsers
import logtools.parsers2
from ._config import interpolate_config, AttrDict, setLoglevel
from ._config import checkDpath

from .parsers2 import FileFormat , TraditionalFileFormat, ForwardFormat
from .parsers2 import TraditionalForwardFormat
from .utils    import getObj

checkDpath()

__all__ = ['logparse_parse_args', 'logparse', 'logparse_main']


def logparse_parse_args():
    parser = OptionParser()
    parser.add_option("-p", "--parser", dest="parser", default=None,
                      help="Log format parser (e.g 'CommonLogFormat'). See documentation for available parsers.")  # noqa
    parser.add_option("-F", "--format", dest="format", default=None,
                      help="Format string. Used by the parser (e.g AccessLog format specifier)")  # noqa
    parser.add_option("-f", "--field", dest="field", default=None,
                      help="Parsed Field index to output")
    parser.add_option("-i", "--ignore", dest="ignore", default=None, action="store_true",  # noqa
                      help="Ignore missing fields errors (skip lines with missing fields)")  # noqa
    parser.add_option("-H", "--header", dest="header", default=None, action="store_true",  # noqa
                      help="Prepend a header describing the selected fields to output.")  # noqa

    parser.add_option("-P", "--profile", dest="profile", default='logparse',
                      help="Configuration profile (section in configuration file)")  # noqa

    parser.add_option("-R", "--raw", dest="raw", default=None, action="store_true",
                      help="When set output is not encoded for UTF-8")  
                      ## default kept for compatibility

    # logging level for debug and other information
    parser.add_option("-s","--sym" , type = str,
                                  dest="logLevSym",
                                  help="logging level (symbol)")

    parser.add_option("-n","--num" , type=int ,
                                  dest="logLevVal",
                                  help="logging level (value)")


    options, args = parser.parse_args()

    # Interpolate from configuration
    options.parser = interpolate_config(options.parser, options.profile, 'parser')
    options.format = interpolate_config(options.format, options.profile, 'format',
                                        default=False)
    options.field = interpolate_config(options.field, options.profile, 'field')
    options.ignore = interpolate_config(options.ignore, options.profile, 'ignore',
                                        default=False, type=bool)
    options.header = interpolate_config(options.header, options.profile, 'header',
                                        default=False, type=bool)
    options.raw = interpolate_config(options.raw, options.profile, 'raw')


    # Set the logging level
    setLoglevel(options)

    return AttrDict(options.__dict__), args


def logparse(options, args, fh):
    """Parse given input stream using given
    parser class and emit specified field(s)"""

    field = options.field
    logtools.parsers2.addConfigFileSection()

    
    parser = getObj(options.parser, (logtools.parsers, logtools.parsers2))()
     
    if options.get('format', None):
        parser.set_format(options.format)

    keyfunc = None
    keys = None
    if isinstance(options.field, int) or \
       (isinstance(options.field, str) and options.field.isdigit()):
        # Field given as integer (index)
        field = int(options.field) - 1
        key_func = lambda x: parser(x.strip()).by_index(field, raw=True)
        keys = [options.field]
    else:
        if isinstance(parser, logtools.parsers2.JSONParserPlus):
            key_func = logtools.parsers2.dpath_getter_gen(parser, options.field, options)
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
                key_func = logtools.parsers.multikey_getter_gen(parser, keys,
                                                                is_indices=is_indices)

    if options.header is True:
        yield '\t'.join(keys)

    for line in fh:
        try:
            yield key_func(line)
        except KeyError as exc:
            # Could not find user-specified field
            logging.warn("Could not match user-specified fields: %s", exc)
        except ValueError as exc:
            # Could not parse the log line
            if options.ignore:
                logging.debug("Could not match fields for parsed line: %s", line)
                continue
            else:
                logging.error("Could not match fields for parsed line: %s", line)
                raise


def logparse_main():
    """Console entry-point"""
    options, args = logparse_parse_args()
    
    for row in logparse(options, args, fh=sys.stdin):
        if row:
            if isinstance(row, dict):
                json.dump(row, sys.stdout)
            elif options.raw:
                print(row)
            else:
                print( row.encode('ascii', 'ignore') )
    return 0
