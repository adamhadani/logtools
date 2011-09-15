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
logtools._sumstat

Generates summary statistics
for a given logfile of the form:

<count> <value>

logfile is expected to be sorted by count
"""

import re
import sys
import locale
import logging

from time import time
from itertools import imap
from datetime import datetime
from optparse import OptionParser
from urlparse import parse_qs, urlsplit

from prettytable import PrettyTable

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['sumstat_parse_args', 'sumstat', 'sumstat_main']

locale.setlocale(locale.LC_ALL, "")

def arith_mean(values):
    """Computes the arithmetic mean of a list of numbers"""
    return sum(values, 0.0) / len(values)

def sumstat_parse_args():
    usage = "%prog -d <delimiter> [--reverse]"
    parser = OptionParser(usage=usage)
    parser.add_option("-r", "--reverse", dest="reverse", action="store_true",
                      help="Reverse ordering of entries (toggle between increasing/decreasing sort order")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")    

    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()
    
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter')
    options.reverse = interpolate_config(options.reverse, options.profile, 'reverse', type=bool, default=False)

    return AttrDict(options.__dict__), args


def sumstat(fh, delimiter, reverse=False, **kwargs):
    counts = []
    N, M = 0, 0

    for line in imap(lambda x: x.strip(), fh):
        try:
            count, val = line.split(delimiter)[:2]
        except ValueError:
            logging.error("Exception while trying to parse log line: '%s', skipping", line)
        else:
            count = int(count)
            counts.append(count)
            M += 1
            N += count
            
    if reverse is True:
        logging.info("Reversing row ordering")
        counts.reverse()
    
    avg = arith_mean(counts)
    minv, maxv = min(counts), max(counts)
    
    
    # Percentiles
    percentiles_idx = [M/10, M/4, M/2, 3*M/4, 9*M/10, 95*M/100, 99*M/100, 999*M/1000]
    percentiles = map(lambda x: "%d (Idx: %s)" % \
                      (counts[x], locale.format('%d', x, True)), 
                      percentiles_idx)
    
    S10th, S25th, S40th, S50th, S75th, S90th = None, None, None, None, None, None
    accum = 0.
    for idx, c in enumerate(reversed(counts)):
        accum += c
        if not S10th and accum/N >= 0.1:
            S10th = idx+1            
        elif not S25th and accum/N >= 0.25:
            S25th = idx+1       
        elif not S40th and accum/N >= 0.4:
            S40th = idx+1                 
        elif not S50th and accum/N >= 0.5:
            S50th = idx+1
        elif not S75th and accum/N >= 0.75:
            S75th = idx+1            
        elif not S90th and accum/N >= 0.9:
            S90th = idx+1
            
    return {
        "M": M,
        "N": N,
        "avg": avg,
        "min": minv,
        "max": maxv,
        "percentiles": percentiles,
        "cover": [S10th, S25th, S40th, S50th, S75th, S90th]
        }
    

def sumstat_main():
    """Console entry-point"""
    options, args = sumstat_parse_args()
    stat_dict = sumstat(fh=sys.stdin, *args, **options)
    
    table = PrettyTable()
    table.set_field_names([
        "Num. Samples (N)",
        "Num. Values (M)",
        "Min. Value",
        "Max. Value",
        "Average Value",
        "10th Percentile",
        "25th Percentile",
        "50th Percentile",
        "75th Percentile",
        "90th Percentile",
        "95th Percentile",
        "99th Percentile",
        "99.9th Percentile"
    ])            
    table.add_row(
        map(lambda x: locale.format('%d', x, True), [stat_dict['N'], stat_dict['M']]) + \
        [stat_dict['min'], stat_dict['max'], stat_dict['avg']] + \
        stat_dict['percentiles']
    )
    table.printt()

    S10th, S25th, S40th, S50th, S75th, S90th = stat_dict['cover']
    M = stat_dict['M']
    print "10%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S10th, True), 100.*S10th/M)
    print "25%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S25th, True), 100.*S25th/M)
    print "40%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S40th, True), 100.*S40th/M)    
    print "50%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S50th, True), 100.*S50th/M)
    print "75%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S75th, True), 100.*S75th/M)
    print "90%% of Sample Volume is encompassed within the top %s (%.4f%%) sample values" % \
          (locale.format("%d", S90th, True), 100.*S90th/M)
    
    return 0
