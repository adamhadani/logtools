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
logtools.parsers
Parsers for some common log formats, e.g Common Log Format (CLF).
These parsers can be used both programmaticaly as well as by the 
logtools command-line tools to meaningfully parse log fields 
from standard formats.
"""
import os
import re
import sys
import logging
from functools import partial
from datetime import datetime
from abc import ABCMeta, abstractmethod
import json

from _config import AttrDict

__all__ = ['multikey_getter_gen', 'unescape_json', 'LogParser', 'JSONParser', 'LogLine',
           'AccessLog', 'CommonLogFormat']


def multikey_getter_gen(parser, keys, is_indices=False, delimiter="\t"):
    """Generator meta-function to return a function
    parsing a logline and returning multiple keys (tab-delimited)"""
    if is_indices:
        keys = map(int, keys)
        
    def multikey_getter(line, parser, keyset):
        data = parser(line.strip())
        return delimiter.join((unicode(data[k]) for k in keyset))
    
    def multiindex_getter(line, parser, keyset):
        data = parser(line.strip())
        return delimiter.join((unicode(data.by_index(idx-1, raw=True)) for idx in keys))

    if is_indices is True:
        # Field indices
        return partial(multiindex_getter, parser=parser, keyset=keys)
    else:
        # Field names
        return partial(multikey_getter, parser=parser, keyset=keys)

def unescape_json(s):
    """Unescape a string that was previously encoded into JSON.
    This unescapes forward slashes (optional in JSON standard),
    backslashes and double quotes"""
    return s.replace("\\/", '/').replace('\\"', '"').decode('string_escape')
    
class LogParser(object):
    """Base class for all our parsers"""
    __metaclass__ = ABCMeta

    def __call__(self, line):
        """Callable interface"""
        return self.parse(line)

    @abstractmethod
    def parse(self, line):
        """Parse a logline"""
        
    def set_format(self, format):
        """Set a format specifier for parser.
        Some parsers can use this to specify
        a format string"""
        
        
class LogLine(dict):
    """Instrumented dictionary that allows
    convenient access to a parsed log lines,
    using key-based lookup / index-based / raw / parsed"""
    
    def __init__(self, fieldnames=None):
        """Initialize logline. This class can be reused
        across multiple input lines by using the clear()
        method after each invocation"""
        
        self._fieldnames = None
        
        if fieldnames:
            self.fieldnames = fieldnames
            
    @property
    def fieldnames(self):
        """Getter method for the field names"""
        return self._fieldnames
            
    @fieldnames.setter
    def fieldnames(self, fieldnames):
        """Set the log format field names"""
        self._fieldnames = dict(enumerate(fieldnames))
        
    def by_index(self, i, raw=False):
        return self.by_key(self._fieldnames[i], raw=raw)
    
    def by_key(self, key, raw=False):
        """Return the i-th field parsed"""
        val = None
        
        if raw is True:
            return self[key]
        
        if key == '%t':
            val = datetime.strptime(self[key][1:-7], '%d/%b/%Y:%H:%M:%S')
        else:
            val = self[key]
        return val
        

class JSONParser(LogParser):
    """Parser implementation for JSON format logs"""
    
    def __init__(self):
        LogParser.__init__(self)
        self._logline_wrapper = LogLine()
        
    def parse(self, line):
        """Parse JSON line"""
        parsed_row = json.loads(line)
        
        data = self._logline_wrapper

        # This is called for every log line - This is because
        # JSON logs are generally schema-less and so fields
        # can change between lines.
        self._logline_wrapper.fieldnames = parsed_row.keys()
            
        data.clear()
        for k, v in parsed_row.iteritems():
            data[k] = v

        return data
    

class AccessLog(LogParser):
    """Apache access_log logfile parser. This can
    consume arbitrary Apache log field directives. see
    http://httpd.apache.org/docs/1.3/logs.html#accesslog"""

    def __init__(self, format=None):
        LogParser.__init__(self)
        
        self.fieldnames    = None
        self.fieldselector = None
        self._logline_wrapper = None
        
        if format:
            self.fieldselector = self._parse_log_format(format)
            self._logline_wrapper = LogLine(self.fieldnames)     

    def set_format(self, format):
        """Set the access_log format"""
        self.fieldselector = self._parse_log_format(format)
        self._logline_wrapper = LogLine(self.fieldnames)     
        
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
        findpercent = re.compile(r'^%.*t$')
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

        return _regex

    
class CommonLogFormat(AccessLog):
    """
    Parse the CLF Format, defined as:
    %h %l %u %t \"%r\" %>s %b
    See http://httpd.apache.org/docs/1.3/logs.html#accesslog
    """

    def __init__(self):
        AccessLog.__init__(self, format='%h %l %u %t "%r" %>s %b')
        