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
logtools.parers
Parsers for some common log formats, e.g 
Common Log Format (CLF) etc.
These parsers can be used both programmaticaly
as well as by the logtools command-line tools to
meaningfully parse log fields from standard formats.
"""
import os
import re
import sys
import logging
from datetime import datetime
from abc import ABCMeta, abstractmethod

__all__ = ['AccessLog', 'CommonLogFormat']


class LogParser(object):
    """Base class for all our parsers"""
    __metaclass__ = ABCMeta

    def __call__(self, line):
        """Callable interface"""
        return self.parse(line)

    @abstractmethod
    def parse(self, line):
        """Parse a logline"""

class AccessLogLine(dict):
    """Instrumented dictionary that allows
    convenient access to a parsed access_log line,
    using key-based lookup / index-based / raw / parsed"""
    
    def __init__(self, fieldnames):
        self._fieldnames = dict(enumerate(fieldnames))
        
    def by_index(self, i):
        return self.by_key(self._fieldnames[i])
    
    def by_key(self, key):
        """Return the i-th field parsed"""
        val = None
        if key == '%t':
            val = datetime.strptime(self[key][1:-7], '%d/%b/%Y:%H:%M:%S')
        else:
            val = self[key]
        return val
        
        
class AccessLog(LogParser):
    """Apache access_log logfile parser. This can
    consume arbitrary Apache log field directives. see
    http://httpd.apache.org/docs/1.3/logs.html#accesslog"""

    def __init__(self, format):
        LogParser.__init__(self)
        
        self.fieldnames    = None
        self.fieldselector = self._parse_log_format(format)
        self._logline_wrapper = AccessLogLine(self.fieldnames)
        

    def parse(self, logline):
        """
        Parse log line into structured row.
        Will raise ParseError Exception when
        parsing failed.
        """
        match = self.fieldselector.match(logline)
        if match:
            data = self._logline_wrapper
            data.clear()
            for k, v in zip(self.fieldnames, match.groups()):
                data[k] = v
            return data                
        else:
            raise ValueError("Could not parse log line: '%s'" % logline)

    def _parse_log_format(self, format):
        """This code piece is based on the apachelogs 
        python/perl projects. Raises an exception if 
        it couldn't compile the generated regex"""
        format = format.strip()
        format = re.sub('[ \t]+',' ',format)

        subpatterns = []

        findquotes = re.compile(r'^"')
        findreferreragent = re.compile('Referer|User-Agent')
        findpercent = re.compile('^%.*t$')
        lstripquotes = re.compile(r'^"')
        rstripquotes = re.compile(r'"$')
        self.fieldnames = []

        for element in format.split(' '):
            hasquotes = 0
            if findquotes.match(element): 
                hasquotes = 1

            if hasquotes:
                element = lstripquotes.sub('', element)
                element = rstripquotes.sub('', element)

            self.fieldnames.append(element)

            subpattern = '(\S*)'

            if hasquotes:
                if element == '%r' or findreferreragent.search(element):
                    subpattern = r'\"([^"\\]*(?:\\.[^"\\]*)*)\"'
                else:
                    subpattern = r'\"([^\"]*)\"'

            elif findpercent.search(element):
                subpattern = r'(\[[^\]]+\])'

            elif element == '%U':
                subpattern = '(.+?)'

            subpatterns.append(subpattern)

        _pattern = '^' + ' '.join(subpatterns) + '$'
        _regex = re.compile(_pattern)

        print _regex.pattern
        return _regex

    
class CommonLogFormat(AccessLog):
    """
    Parse the CLF Format, defined as:
    %h %l %u %t \"%r\" %>s %b
    See http://httpd.apache.org/docs/1.3/logs.html#accesslog
    """

    def __init__(self):
        AccessLog.__init__(self, format='%h %l %u %t "%r" %>s %b')
        