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
logtools._tail
A tail-like utility that allows tailing via time-frames and more complex
expressions.
"""
import re
import sys
import string
import logging
from itertools import imap
from functools import partial
from operator import and_
from datetime import datetime
from optparse import OptionParser

import dateutil.parser

from _config import logtools_config, interpolate_config, AttrDict
import logtools.parsers

__all__ = ['logtail_parse_args', 'logtail', 
           'logtail_main']

def _is_match_full(val, date_format, dt_start):
    """Perform filtering on line"""
    dt = datetime.strptime(val, date_format)
    if dt >= dt_start:
        return True
    return False    


def logtail_parse_args():
    usage = "%prog " \
          "--date-format <date_format>" \
          "--start-date <start_date> "

    
    parser = OptionParser(usage=usage)

    parser.add_option("--date-format", dest="date_format",
            help="Date format (Using date utility notation, e.g '%Y-%m-%d')")
    parser.add_option("--start-date", dest="start_date",
            help="Start date expression (e.g '120 minutes ago')")

    parser.add_option("--parser", dest="parser",
                      help="Feed logs through a parser. Useful when reading encoded/escaped formats (e.g JSON) and when " \
                      "selecting parsed fields rather than matching via regular expression.")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation (when not using a --parser)")        
    parser.add_option("-f", "--field", dest="field",
                      help="Index of field to use for filtering against")
    parser.add_option("-p", "--print", dest="printlines", action="store_true",
                      help="Print non-filtered lines")    

    parser.add_option("-P", "--profile", dest="profile", default='logtail',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.date_format  = interpolate_config(options.date_format, options.profile, 'date_format')
    options.start_date  = interpolate_config(options.start_date, options.profile, 'start_date')
    options.field  = interpolate_config(options.field, options.profile, 'field')
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter', default=' ')    
    options.parser = interpolate_config(options.parser, options.profile, 'parser', 
                                        default=False) 
    options.printlines = interpolate_config(options.printlines, 
                        options.profile, 'print', default=False, type=bool)     
    
    if options.parser and not options.field:
        parser.error("Must supply --field parameter when using parser-based matching.")

    return AttrDict(options.__dict__), args

def logtail(fh, date_format, start_date, field, parser=None, delimiter=None,
            **kwargs):
    """Tail rows from logfile, based on complex expressions such as a
    date range."""
            
    dt_start = dateutil.parser.parse(start_date)
    _is_match = partial(_is_match_full, date_format=date_format, dt_start=dt_start)
   
    _is_match_func = _is_match
    if parser:
        # Custom parser specified, use field-based matching
        parser = eval(parser, vars(logtools.parsers), {})()
        is_indices = field.isdigit()
        if is_indices:
            # Field index based matching
            def _is_match_func(line):
                parsed_line = parser(line)
                return _is_match(parsed_line.by_index(field))
        else:
            # Named field based matching
            def _is_match_func(line):
                parsed_line = parser(line)
                return _is_match(parsed_line.by_index(field))
    else:
        # No custom parser, field/delimiter-based extraction
        def _is_match_func(line):
            val = line.split(delimiter)[int(field)-1]
            return _is_match(val)
                
    num_lines=0
    num_filtered=0
    num_nomatch=0
    for line in imap(lambda x: x.strip(), fh):
        try:
             is_match = _is_match_func(line)
        except (KeyError, ValueError):
            # Parsing error
            logging.warn("No match for line: %s", line)
            num_nomatch +=1
            continue
        else:
            if not is_match:
                logging.debug("Filtering line: %s", line)
                num_filtered += 1
                continue

            num_lines+=1
            yield line

    logging.info("Number of lines after filtering: %s", num_lines)
    logging.info("Number of lines filtered: %s", num_filtered)        
    if num_nomatch:
        logging.info("Number of lines could not match on: %s", num_nomatch)

    return

def logtail_main():
    """Console entry-point"""
    options, args = logtail_parse_args()
    if options.printlines:
        for line in logtail(fh=sys.stdin, *args, **options):
            print line
    else:
        for line in logtail(fh=sys.stdin, *args, **options): 
            pass

    return 0

