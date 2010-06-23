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
logtools._plot
Plotting methods for logfiles
"""

import os
import re
import sys
import logging
from itertools import imap
from random import randint
from optparse import OptionParser

from _config import logtools_config, interpolate_config

__all__ = ['logplot_parse_args', 'logplot', 'logplot_main']

def logplot_parse_args():
    parser = OptionParser()
    parser.add_option("-b", "--backend", dest="backend",  
                      help="Backend to use for plotting. See --help for available backends.")
    parser.add_option("-f", "--field", dest="field", type=int,
                      help="Index of field to use as input for generating plot")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation.")
    
    options, args = parser.parse_args()

    # Interpolate from configuration
    options.backend  = interpolate_config(options.backend, 'logplot', 'backend')
    options.field  = int(interpolate_config(options.field, 'logplot', 'field'))
    options.delimiter  = interpolate_config(options.delimiter, 'logplot', 'delimiter')

    return options, args

def logplot(options, args, fh):
    """Plot some index defined over the logstream,
    using user-specified backend"""


def logplot_main():
    """Console entry-point"""
    options, args = logplot_parse_args()
    logsample(options, args, fh=sys.stdin.readlines())
    return 0
