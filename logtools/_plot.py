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
import locale
import logging
from itertools import imap
from random import randint
from operator import itemgetter
from optparse import OptionParser
from abc import ABCMeta, abstractmethod

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['logplot_parse_args', 'logplot', 'logplot_main']

locale.setlocale(locale.LC_ALL, "")

class PlotBackend(object):
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def plot(self, options, args, fh):
        """Plot using backend implementation"""
        
class GChartBackend(PlotBackend):
    """Google Chart API plotting backend.
    uses the pygooglechart python package"""
    
    def __init__(self):
        PlotBackend.__init__(self)
        
    def plot(self, options, args, fh):
        """Plot using google charts api"""
        try:
            import pygooglechart
        except ImportError:
            logging.error("pygooglechart Python package must be installed to use the 'gchart' backend")
            sys.exit(-1)

        try:
            chart = {
                'pie': self._plot_pie,
                'line': self._plot_line
            }[options.type](options, args, fh)
        except KeyError:
            raise KeyError("Invalid plot type: '%s'" % options.type)
        else:
            if options.get('title', None):
                chart.set_title(options.title)
            if options.get('output', None):
                chart.download(options.output)
                
            return chart

    def _plot_line(self, options, args, fh):
        """Plot a line chart"""
        from pygooglechart import Chart, SimpleLineChart, Axis
        
        delimiter = options.delimiter
        field = options.field
        
        pts = []
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = int(splitted_line.pop(field-1))
            pts.append((k, ' '.join(splitted_line)))
        
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
                        
        max_y = max((v for v, label in pts))  
        chart = SimpleLineChart(options.width, options.height,y_range=[0, max_y])
        
        # Styling
        chart.set_colours(['0000FF'])
        chart.fill_linear_stripes(Chart.CHART, 0, 'CCCCCC', 0.2, 'FFFFFF', 0.2)        
        chart.set_grid(0, 25, 5, 5)
        
        data, labels = zip(*pts)
        chart.add_data(data)
        
        # Axis labels
        chart.set_axis_labels(Axis.BOTTOM, labels)
        left_axis = range(0, max_y + 1, 25)
        left_axis[0] = ''
        chart.set_axis_labels(Axis.LEFT, left_axis)
        
        return chart
        
    def _plot_pie(self, options, args, fh):
        """Plot a pie chart"""
        from pygooglechart import PieChart3D, PieChart2D

        delimiter = options.delimiter
        field = options.field
                
        chart = PieChart2D(options.width, options.height)
        pts = []
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = int(splitted_line.pop(field-1))
            pts.append((k, ' '.join(splitted_line), locale.format('%d', k, True)))
            
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
            
        if not pts:
            raise ValueError("No data to plot")
        
        data, labels, legend = zip(*pts)
        chart.add_data(data)
        chart.set_pie_labels(labels)
        if options.get('legend', None) is True:
            chart.set_legend(map(str, legend))
                        
        return chart
    

def logplot_parse_args():
    parser = OptionParser()
    parser.add_option("-b", "--backend", dest="backend",  
                      help="Backend to use for plotting. Currently available backends: 'gchart'")
    parser.add_option("-T", "--type", dest="type",  
                      help="Chart type. Available types: 'pie', 'histogram', 'line'." \
                      "Availability might differ due to backend.")    
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
    parser.add_option("-t", "--title", dest="title",
                      help="Plot Title")     
    
    parser.add_option("-P", "--profile", dest="profile", default='logplot',
                      help="Configuration profile (section in configuration file)")
    
    options, args = parser.parse_args()

    # Interpolate from configuration
    options.backend  = interpolate_config(options.backend, options.profile, 'backend')
    options.type = interpolate_config(options.type, options.profile, 'type')
    options.field  = interpolate_config(options.field, options.profile, 'field', type=int)
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter')
    options.output = interpolate_config(options.output, options.profile, 'output', default=False)
    options.width = interpolate_config(options.width, options.profile, 'width', type=int)
    options.height = interpolate_config(options.height, options.profile, 'height', type=int)    
    options.limit = interpolate_config(options.limit, options.profile, 'limit', type=int, default=False) 
    options.legend = interpolate_config(options.legend, options.profile, 'legend', type=bool, default=False) 
    options.title = interpolate_config(options.title, options.profile, 'title', default=False)

    return AttrDict(options.__dict__), args

def logplot(options, args, fh):
    """Plot some index defined over the logstream,
    using user-specified backend"""            
    return {
        "gchart":  GChartBackend()
    }[options.backend].plot(options, args, fh)

def logplot_main():
    """Console entry-point"""
    options, args = logplot_parse_args()
    logplot(options, args, fh=sys.stdin)
    return 0
