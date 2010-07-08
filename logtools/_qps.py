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
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['qps_parse_args', 'qps', 'qps_main']

def qps_parse_args():
    usage = "%prog " \
        "-r <timestamp_reg_exp> " \
        "-f <timestamp_format_string> " \
        "-t <sliding_window_interval_seconds>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-r", dest="ts_re", default=None, 
                      help="Regular expression to timestamp field.")
    parser.add_option("-f", dest="ts_format", default=None, 
                      help="Timestamp datetime format (See Python datetime format strings).")
    parser.add_option("-t", dest="time_delta", default=None, 
                      help="Sliding window interval (in seconds)")
    
    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.ts_re = interpolate_config(options.ts_re, 
                    options.profile, 'ts_re')    
    options.ts_format = interpolate_config(options.ts_format, 
                    options.profile, 'ts_format')
    options.time_delta = interpolate_config(options.time_delta, 
                    options.profile, 'time_delta', type=int)    
    
    return AttrDict(options.__dict__), args

def qps(options, args, fh):
    """Calculate QPS from input stream based on
    parsing of timestamps and using a sliding time window"""
    
def qps_main():
    """Console entry-point"""
    options, args = qps_parse_args()
    for qps_info in qps(options, args, fh=sys.stdin.readlines()):
        print >> sys.stderr, qps_info
        
    return 0
