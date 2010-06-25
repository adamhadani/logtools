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
from random import randint, random
from optparse import OptionParser
from heapq import heappush, heappop, heapreplace

from _config import logtools_config, interpolate_config

__all__ = ['logsample_parse_args', 'logsample', 'logsample_weighted', 'logsample_main']

def logsample_parse_args():
    parser = OptionParser()
    parser.add_option("-n", "--num-samples", dest="num_samples", type=int, 
                      help="Number of samples to produce")
    parser.add_option("-w", "--weighted", dest="weighted", action="store_true",
                      help="Use Weighted Reservoir Sampling (needs -f and -d parameters)")

    parser.add_option("-P", "--profile", dest="profile", default='logsample',
                      help="Configuration profile (section in configuration file)")
    
    options, args = parser.parse_args()

    # Interpolate from configuration
    options.num_samples  = interpolate_config(options.num_samples, 
                                options.profile, 'num_samples', type=int)
    options.weighted  = interpolate_config(options.weighted, 
                                options.profile, 'weighted', type=bool, default=False)    

    return AttrDict(options.__dict__), args

def logsample(options, args, fh):
    """Use a Reservoir Sampling algorithm
    to sample uniformly random lines from input stream."""
    R = []
    N = options.num_samples
    
    for i, k in enumerate(fh):
        if i < N:
            R.append(k)
        else:
            r = randint(0,i)
            if r < N:
                R[r] = k

    # Emit output
    for record in R:
        yield record.strip()

def logsample_weighted(options, args, fh):
    """Implemented Weighted Reservoir Sampling, assuming integer weights.
    See Weighted random sampling with a reservoir, Efraimidis et al."""
    
    N = options.num_samples
    delimiter = options.delimiter
    # NOTE: Convert to 0-based indexing since we expose as 1-based
    field = options.field-1
    
    R = []
    min_val = float("inf")
    i = 0
    
    for line in fh:
        w = int(line.split(delimiter)[field])
        if w < 1: 
            continue
        
        r = random()
        k = r ** (1./w)            
        
        if i < N:
            heappush(R, (k, line))
            if k < min_val:
                min_val = k
        else:
            if k > min_val:
                # Replace smallest item in record list
                heapreplace(R, (k, line))
        i+=1
                
    # Emit output
    for key, record in R:
        yield key, record.strip()

        
def logsample_main():
    """Console entry-point"""
    options, args = logsample_parse_args()
    
    if options.weighted is True:
        for k, r in logsample_weighted(options, args, fh=sys.stdin.readlines()):
            print r
    else:
        for r in logsample(options, args, fh=sys.stdin.readlines()):
            print r
        
    return 0

