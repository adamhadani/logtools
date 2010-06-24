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
from operator import itemgetter
from optparse import OptionParser

from _config import logtools_config, interpolate_config

__all__ = ['logplot_parse_args', 'logplot', 'logplot_main']

def logplot_parse_args():
    parser = OptionParser()
    parser.add_option("-b", "--backend", dest="backend",  
                      help="Backend to use for plotting. See --help for available backends")
    parser.add_option("-f", "--field", dest="field", type=int,
                      help="Index of field to use as input for generating plot")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")
    parser.add_option("-o", "--output", dest="output", help="Output filename")    
    parser.add_option("-W", "--width", dest="width", type=int, help="Plot Width")   
    parser.add_option("-H", "--height", dest="height", type=int, help="Plot Height")       
    parser.add_option("-L", "--limit", dest="limit", type=int, 
                      help="Only plot the top N rows, sorted decreasing by key")        
    parser.add_option("-l", "--legend", dest="legend", action="store_true", 
                      help="Render Plot Legend")       
    
    options, args = parser.parse_args()

    # Interpolate from configuration
    options.backend  = interpolate_config(options.backend, 'logplot', 'backend')
    options.field  = interpolate_config(options.field, 'logplot', 'field', type=int)
    options.delimiter  = interpolate_config(options.delimiter, 'logplot', 'delimiter')
    options.output = interpolate_config(options.output, 'logplot', 'output')
    options.width = interpolate_config(options.width, 'logplot', 'width', type=int)
    options.height = interpolate_config(options.height, 'logplot', 'height', type=int)    
    options.limit = interpolate_config(options.limit, 'logplot', 'limit', type=int, default=False) 
    options.legend = interpolate_config(options.legend, 'logplot', 'legend', type=bool, default=False) 

    return options, args

def logplot(options, args, fh):
    """Plot some index defined over the logstream,
    using user-specified backend"""
    return {
        "gchart":  logplot_gchart
    }[options.backend](options, args, fh)


def logplot_gchart(options, args, fh):
    """Plot using google charts api"""
    try:
        import pygooglechart
    except ImportError:
        logging.error("Must have pygooglechart package to use gchart")
        return
    from pygooglechart import PieChart3D, PieChart2D
    
    delimiter = options.delimiter
    field = options.field
    
    chart = PieChart2D(options.width, options.height)
    pts = []
    for l in imap(lambda x: x.strip(), fh):
        splitted_line = l.split(delimiter)
        k = int(splitted_line.pop(field-1))
        pts.append((k, ' '.join(splitted_line), k))
        
    if options.limit:
        # Only wanna use top N samples by key, sort and truncate
        pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
        
    data, labels, legend = zip(*pts)
    chart.add_data(data)
    chart.set_pie_labels(labels)
    if options.legend is True:
        chart.set_legend(map(str, legend))
    chart.download(options.output)
    
def logplot_main():
    """Console entry-point"""
    options, args = logplot_parse_args()
    logplot(options, args, fh=sys.stdin.readlines())
    return 0
