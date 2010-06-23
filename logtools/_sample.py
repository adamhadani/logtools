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
logtools._sample
Sampling tools for logfiles
"""

import os
import re
import sys
import logging
from itertools import imap
from random import randint
from optparse import OptionParser

from _config import logtools_config, interpolate_config

def logsample_parse_args():
    parser = OptionParser()
    parser.add_option("-n", "--num-samples", dest="num_samples", type=int, 
                      help="Number of samples to produce")

    options, args = parser.parse_args()

    # Interpolate from configuration
    options.num_samples  = int(interpolate_config(options.num_samples, 
                                                  'logsample', 'num_samples'))

    return options, args

def logsample(options, args, fh):
    """Use a Reservoir Sampling algorithm
    to sample uniformly random lines from input stream."""
    R = []
    N = options.num_samples
    
    for i, k in enumerate(imap(lambda x: x.strip(), fh)):
        if i < N:
            R.append(k)
        else:
            r = randint(0,i)
            if r < N:
                R[r] = k

    # Emit output
    for r in R:
        print r
        
    return R

def logsample_main():
    """Console entry-point"""
    options, args = logsample_parse_args()
    logsample(options, args, fh=sys.stdin.readlines())
    return 0

