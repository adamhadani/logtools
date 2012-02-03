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
logtools._qps
Compute QPS estimates based on parsing of timestamps from logs on
sliding time windows.
"""
import re
import sys
import logging
from time import time
from itertools import imap
from datetime import datetime
from optparse import OptionParser

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['qps_parse_args', 'qps', 'qps_main']

def qps_parse_args():
    usage = "%prog " \
          "-d <delimiter_character> " \
          "-F <timestamp_format_string> " \
          "-t <sliding_window_interval_seconds>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-r", "--re", dest="dt_re", default=None, 
                    help="Regular expression to lookup datetime in logrow")
    parser.add_option("-F", "--dateformat", dest="dateformat",
                      help="Format string for parsing date-time field (used with --datetime)")        
    parser.add_option("-W", '--window-size', dest="window_size", type=int, default=None, 
                      help="Sliding window interval (in seconds)")
    parser.add_option("-i", "--ignore", dest="ignore", default=None, action="store_true",
                    help="Ignore missing datefield errors (skip lines with missing/unparse-able datefield)")      

    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.dt_re  = interpolate_config(options.dt_re, options.profile, 're')    
    options.dateformat = interpolate_config(options.dateformat, 
                                            options.profile, 'dateformat', default=False)    
    options.window_size = interpolate_config(options.window_size, 
                                            options.profile, 'window_size', type=int)
    options.ignore = interpolate_config(options.ignore, options.profile, 'ignore', 
                                        default=False, type=bool)    

    return AttrDict(options.__dict__), args

def qps(fh, dt_re, dateformat, window_size, ignore, **kwargs):
    """Calculate QPS from input stream based on
    parsing of timestamps and using a sliding time window"""
    
    _re = re.compile(dt_re)
    t0=None
    samples=[]

    # Populate with first value
    while not t0:
        line = fh.readline()
        if not line:
            return
        try:
            t = datetime.strptime(_re.match(line).groups()[0], dateformat)
        except (AttributeError, KeyError, TypeError, ValueError):
            if ignore:
                logging.debug("Could not match datefield for parsed line: %s", line)
                continue
            else:
                logging.error("Could not match datefield for parsed line: %s", line)
                raise            
        else:
            t0 = t
            samples.append(t0)
    
    # Run over rest of input stream
    for line in imap(lambda x: x.strip(), fh):
        try:
            t = datetime.strptime(_re.match(line).groups()[0], dateformat)
        except (AttributeError, KeyError, TypeError, ValueError):
            if ignore:
                logging.debug("Could not match datefield for parsed line: %s", line)
                continue
            else:
                logging.error("Could not match datefield for parsed line: %s", line)
                raise            
        else:
            dt = t-t0
            if dt.seconds > window_size or dt.days:
                if samples:
                    num_samples = len(samples)
                    yield {
                        "qps": float(num_samples)/window_size,
                        "start_time": samples[0],
                        "end_time": samples[-1],
                        "num_samples": num_samples
                    }
                t0=t
                samples=[]
            samples.append(t)
            
    # Emit any remaining values
    if samples:
        num_samples = len(samples)
        yield {
            "qps": float(num_samples)/window_size,
            "start_time": samples[0],
            "end_time": samples[-1],
            "num_samples": num_samples
        }        

def qps_main():
    """Console entry-point"""
    options, args = qps_parse_args()
    for qps_info in qps(fh=sys.stdin, *args, **options):
        print >> sys.stdout, "{start_time}\t{end_time}\t{num_samples}\t{qps:.2f}".format(**qps_info)

    return 0
