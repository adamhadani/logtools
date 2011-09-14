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
logtools._filter
Filter rows based on blacklists and field matching.
"""
import re
import sys
import string
import logging
from itertools import imap
from functools import partial
from operator import and_
from optparse import OptionParser

import acora

from _config import logtools_config, interpolate_config, AttrDict
import logtools.parsers

__all__ = ['logfilter_parse_args', 'logfilter', 
           'logfilter_main']

# Used for aho-corasick style matching on word-boundaries.
# Closely mimicks the behavior of the python re module's \w
# character set, however might diverge slightly in case of locale-
# specific character sets.
_word_boundary_chars = set(string.printable)\
                     .difference(string.letters)\
                     .difference(string.digits)\
                     .difference(('_',))


def _is_blacklisted_re_wb(line, delimiter, field, blacklist, re_flags):
    val = line.split(delimiter)[field-1]
    for b in blacklist:
        if re.search(r'\b{0}\b'.format(b), val, re_flags):
            return True
    return False    

def _is_blacklisted_re(line, delimiter, field, blacklist, re_flags):
    val = line.split(delimiter)[field-1]
    for b in blacklist:
        if re.search(r'{0}'.format(b), val, re_flags):
            return True
    return False            

def _is_blacklisted_ac_wb(line, delimiter, field, transform_func, ac):
    val = line.split(delimiter)[field-1]
    L = len(val)
    matches = ac.findall(transform_func(val))
    for match in matches:
        word, pos = match
        l = len(word)
        if (pos == 0 or val[pos-1] in _word_boundary_chars) and \
           (pos+l == L or val[pos+l] in _word_boundary_chars):
            return True
    return False

def _is_blacklisted_ac(line, delimiter, field, transform_func, ac):
    val = line.split(delimiter)[field-1]
    matches = ac.findall(transform_func(val))
    if matches:
        return True
    return False            



def logfilter_parse_args():
    usage = "%prog " \
          "-b <blacklist_file> " \
          "[--reverse]"
    
    parser = OptionParser(usage=usage)

    parser.add_option("-b", "--blacklist", dest="blacklist", default=None, 
                      help="Blacklist (whitelist when in --reverse mode) file")
    parser.add_option("-I", "--ignore-case", dest="ignorecase", action="store_true",
                      help="Ignore case when matching")
    parser.add_option("-W", "--word-boundaries", dest="word_boundaries", action="store_true",
                      help="Only match on word boundaries (e.g start/end of line and/or spaces)")    
    parser.add_option("-A", '--with-acora', dest='with_acora', action="store_true",
                      help="Use Aho-Corasick multiple string pattern matching instead of regexps. Suitable for whole word matching")
    parser.add_option("-r", "--reverse", dest="reverse", action="store_true",
                      help="Reverse filtering")
    parser.add_option("-p", "--print", dest="printlines", action="store_true",
                      help="Print non-filtered lines")    
    parser.add_option("--parser", dest="parser",
                      help="Feed logs through a parser. Useful when reading encoded/escaped formats (e.g JSON) and when " \
                      "selecting parsed fields rather than matching via regular expression.")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation (when not using a --parser)")        
    parser.add_option("-f", "--field", dest="field", type=int,
                      help="Index of field to use for filtering against")

    parser.add_option("-P", "--profile", dest="profile", default='logfilter',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.field  = interpolate_config(options.field, options.profile, 'field', type=int)
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter', default=' ')    
    options.blacklist = open(interpolate_config(options.blacklist, 
                        options.profile, 'blacklist'), "r")
    options.parser = interpolate_config(options.parser, options.profile, 'parser', 
                                        default=False) 
    options.reverse = interpolate_config(options.reverse, 
                        options.profile, 'reverse', default=False, type=bool)
    options.ignorecase = interpolate_config(options.ignorecase, 
                        options.profile, 'ignorecase', default=False, type=bool)
    options.word_boundaries = interpolate_config(options.word_boundaries, 
                        options.profile, 'word_boundaries', default=False, type=bool)        
    options.with_acora = interpolate_config(options.with_acora, 
                        options.profile, 'with_acora', default=False, type=bool)    
    options.printlines = interpolate_config(options.printlines, 
                        options.profile, 'print', default=False, type=bool)     
    
    if options.parser and not options.field:
        parser.error("Must supply --field parameter when using parser-based matching.")

    return AttrDict(options.__dict__), args

def logfilter(fh, blacklist, field, parser=None, reverse=False, 
              delimiter=None, ignorecase=False, with_acora=False, 
              word_boundaries=False, **kwargs):
    """Filter rows from a log stream using a blacklist"""
    
    blacklist = dict.fromkeys([l.strip() for l \
                               in blacklist \
                               if l and not l.startswith('#')])
    re_flags = 0
    
    if ignorecase:
        re_flags = re.IGNORECASE
        
    _is_blacklisted=None
    if with_acora is False:
        # Regular expression based matching
        if word_boundaries:
            _is_blacklisted = partial(_is_blacklisted_re_wb, 
                delimiter=delimiter, field=field, blacklist=blacklist, re_flags=re_flags)
        else:
            _is_blacklisted = partial(_is_blacklisted_re, 
                delimiter=delimiter, field=field, blacklist=blacklist, re_flags=re_flags)                        
    else:
        # Aho-Corasick multiple string pattern matching
        # using the acora Cython library
        builder = acora.AcoraBuilder(*blacklist)
        ac = builder.build()
        _transform_func = lambda x: x
        if ignorecase:
            _transform_func = lambda x: x.lower()
        
        if word_boundaries:
            _is_blacklisted = partial(_is_blacklisted_ac_wb, 
                delimiter=delimiter, field=field, transform_func=_transform_func, ac=ac)
        else:
            _is_blacklisted = partial(_is_blacklisted_ac, 
                delimiter=delimiter, field=field, transform_func=_transform_func, ac=ac)                        
                
    _is_blacklisted_func = _is_blacklisted
    if parser:
        # Custom parser specified, use field-based matching
        parser = eval(parser, vars(logtools.parsers), {})()
        fields = field.split(',')
        is_indices = reduce(and_, (k.isdigit() for k in fields), True)
        if is_indices:
            # Field index based matching
            def _is_blacklisted_func(line):
                parsed_line = parser(line)
                for field in fields:
                    if _is_blacklisted(parsed_line.by_index(field)):
                        return True
                return False
        else:
            # Named field based matching
            def _is_blacklisted_func(line):
                parsed_line = parser(line)
                for field in fields:
                    if _is_blacklisted(parsed_line.by_index(field)):
                        return true
                return False            
            
    num_lines=0
    num_filtered=0
    num_nomatch=0
    for line in imap(lambda x: x.strip(), fh):
        try:
            is_blacklisted = _is_blacklisted_func(line)
        except (KeyError, ValueError):
            # Parsing error
            logging.warn("No match for line: %s", line)
            num_nomatch +=1
            continue
        else:
            if is_blacklisted ^ reverse:
                logging.debug("Filtering line: %s", line)
                num_filtered+=1
                continue

            num_lines+=1
            yield line

    logging.info("Number of lines after filtering: %s", num_lines)
    logging.info("Number of lines filtered: %s", num_filtered)        
    if num_nomatch:
        logging.info("Number of lines could not match on: %s", num_nomatch)

    return

def logfilter_main():
    """Console entry-point"""
    options, args = logfilter_parse_args()
    if options.printlines:
        for line in logfilter(fh=sys.stdin, *args, **options):
            print line
    else:
        for line in logfilter(fh=sys.stdin, *args, **options): 
            pass

    return 0

