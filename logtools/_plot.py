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
import unicodedata
from itertools import imap
from random import randint
from datetime import datetime
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
                'line': self._plot_line,
                'timeseries': self._plot_timeseries
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
        field = options.field-1
        
        pts = []
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = float(splitted_line.pop(field))
            pts.append((k, ' '.join(splitted_line)))
        
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
                        
        max_y = int(max((v for v, label in pts)))
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
        field = options.field-1
                
        chart = PieChart2D(options.width, options.height)
        pts = []
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = int(splitted_line.pop(field))
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
    
    def _plot_timeseries(self, options, args, fh):
        """Plot a timeseries graph"""
        from pygooglechart import Chart, SimpleLineChart, Axis
        
        delimiter = options.delimiter
        field = options.field-1
        datefield = options.datefield-1
        
        pts = []
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            v = float(splitted_line[field])
            t = datetime.strptime(splitted_line[datefield], options.dateformat)
            pts.append((t, v))
        
        if options.get('limit', None):
            # Only wanna use top (earliest) N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
                        
        max_y = int(max((v for t, v in pts)))
        chart = SimpleLineChart(options.width, options.height,y_range=[0, max_y])
        
        # Styling
        chart.set_colours(['0000FF'])
        chart.fill_linear_stripes(Chart.CHART, 0, 'CCCCCC', 0.2, 'FFFFFF', 0.2)        
        chart.set_grid(0, 25, 5, 5)
        
        ts, vals = zip(*pts)
        chart.add_data(vals)
        
        # Axis labels
        chart.set_axis_labels(Axis.BOTTOM, ts)
        left_axis = range(0, max_y + 1, 25)
        left_axis[0] = ''
        chart.set_axis_labels(Axis.LEFT, left_axis)
        
        return chart        

        
class MatplotlibBackend(PlotBackend):
    """Use matplotlib (pylab) for rendering plots"""
    
    def __init__(self):
        PlotBackend.__init__(self)
        
    def plot(self, options, args, fh):
        """Plot using google charts api"""
        try:
            import pylab
        except ImportError:
            logging.error("matplotlib Python package must be installed to use the 'matplotlib' backend")
            sys.exit(-1)
            
        try:
            chart = {
                'hist': self._plot_hist,
                'pie': self._plot_pie,
                'line': self._plot_line,
                'timeseries': self._plot_timeseries
            }[options.type](options, args, fh)
        except KeyError:
            raise KeyError("Invalid plot type: '%s'" % options.type)
        else:
            if options.get('title', None):
                chart.get_axes()[0].set_title(options.title)
            if options.get('output', None):
                chart.savefig(options.output)
                
            return chart 
      
    def _plot_hist(self, options, args, fh):
        """Plot a histogram"""
        import pylab
        
        delimiter = options.delimiter
        field = options.field-1
         
        pts = []
        max_y = -float("inf")
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = float(splitted_line.pop(field))
            pts.append((k, ' '.join(splitted_line)))
            if k > max_y:
                max_y = k
        
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
        
        data, labels = zip(*pts)        
        normed = False
        bins = len(data)/100.
        
        f = pylab.figure()
        pylab.hist(data, bins=bins, normed=normed)
                
        return f
    
    
    def _plot_pie(self, options, args, fh):
        """Plot pie chart"""
        from pylab import figure, pie, legend
        import matplotlib as mpl
        mpl.rc('font', size=8)

        delimiter = options.delimiter
        field = options.field-1
                
        pts = []
        ttl = 0.
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = float(splitted_line.pop(field))
            ttl += k
            pts.append((k, ' '.join(splitted_line), locale.format('%d', k, True)))
        
        
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
            
        if not pts or ttl==0:
            raise ValueError("No data to plot")
        
        data, labels, _legend = zip(*pts)
        data = list(data)
        # Normalize
        for idx, pt in enumerate(data):
            data[idx] /= ttl
        
        f = figure()
        pie(data, labels=labels, autopct='%1.1f%%', shadow=True)
        if options.get('legend', None) is True:        
            legend(_legend, loc=3)
        
        return f
        
    def _plot_line(self, options, args, fh):
        """Line plot using matplotlib"""
        import pylab
        
        delimiter = options.delimiter
        field = options.field-1
         
        pts = []
        max_y = -float("inf")
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            k = float(splitted_line.pop(field))
            label = unicodedata.normalize('NFKD', \
                        unicode(' '.join(splitted_line), 'utf-8')).encode('ascii','ignore')
            pts.append((k, label))
            if k > max_y:
                max_y = k
        
        if options.get('limit', None):
            # Only wanna use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
        
        data, labels = zip(*pts)
        
        f = pylab.figure()
        pylab.plot(xrange(len(data)), data, "*--b")
        if options.get('legend', None):
            pylab.xticks(xrange(len(labels)), labels, rotation=17)
                
        return f
    
    def _plot_timeseries(self, options, args, fh):
        """Line plot using matplotlib"""
        import pylab
        import matplotlib.ticker as ticker
        
        delimiter = options.delimiter
        field = options.field-1
        datefield = options.datefield-1
        
        pts = []
        max_y = -float("inf")
        for l in imap(lambda x: x.strip(), fh):
            splitted_line = l.split(delimiter)
            v = float(splitted_line[field])
            t = datetime.strptime(splitted_line[datefield], options.dateformat)
            pts.append((t, v))
            if v > max_y:
                max_y = v
        
        if options.get('limit', None):
            # Only use top N samples by key, sort and truncate
            pts = sorted(pts, key=itemgetter(0), reverse=True)[:options.limit]
                      
        if not pts:
            raise ValueError("No data to plot")
        
        N = len(pts)
        ts, vals = zip(*pts)
        
        def format_date(x, pos=None):
            thisind = int(max(0, min(x, N)))
            return ts[thisind].strftime(options.dateformat)

        
        f = pylab.figure()
        ax = f.add_subplot(111)
        ax.plot(xrange(len(vals)), vals, "*--b")
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
        f.autofmt_xdate()
                
        return f    

    
def logplot_parse_args():
    parser = OptionParser()
    parser.add_option("-b", "--backend", dest="backend",  
                      help="Backend to use for plotting. Currently available backends: 'gchart', 'matplotlib'")
    parser.add_option("-T", "--type", dest="type",  
                      help="Chart type. Available types: 'pie', 'histogram', 'line'." \
                      "Availability might differ due to backend.")    
    parser.add_option("-f", "--field", dest="field", type=int,
                      help="Index of field to use as main input for plot")
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
    parser.add_option("--datefield", dest="datefield", type=int,
                      help="Index of field to use as date-time source (for timeseries plots)")    
    parser.add_option("--dateformat", dest="dateformat",
                      help="Format string for parsing date-time field (for timeseries plots)")    
    
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
    options.datefield = interpolate_config(options.datefield, options.profile, 'datefield', type=int, default=False)
    options.dateformat = interpolate_config(options.dateformat, options.profile, 'dateformat', default=False)

    return AttrDict(options.__dict__), args

def logplot(options, args, fh):
    """Plot some index defined over the logstream,
    using user-specified backend"""            
    return {
        "gchart":  GChartBackend(),
        "matplotlib": MatplotlibBackend()
    }[options.backend].plot(options, args, fh)

def logplot_main():
    """Console entry-point"""
    options, args = logplot_parse_args()
    logplot(options, args, fh=sys.stdin)
    return 0
