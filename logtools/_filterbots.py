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
logtools._filterbots
Filter bots from logrows based on an ip/host and useragent blacklists.
"""
import re
import sys
import logging
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config

__all__ = ['filterbots_parse_args', 'filterbots', 'filterbots_main']

def filterbots_parse_args():
    usage = "%prog -u <useragents_blacklist_file> -i <ips_blacklist_file> -r <ip_useragent_regexp>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-u", dest="bots_ua", default=None, 
                      help="Bots useragents blacklist file")
    parser.add_option("-i", dest="bots_ips", default=None, 
                      help="Bots ips blacklist file")
    parser.add_option("-r", dest="ip_ua_re", default=None, 
                      help="Regular expression to match IP and useragent field. Should have a 'ip' and 'ua' named groups")
    parser.add_option("-p", "--print", dest="printlines", action="store_true",
                      help="Print non-filtered lines")
    parser.add_option("-R", "--reverse", dest="reverse", action="store_true",
                      help="Reverse filtering")

    options, args = parser.parse_args()

    # Interpolate from configuration and open filehandle
    options.bots_ua  = open(interpolate_config(options.bots_ua, 'filterbots', 'bots_ua'), "r")
    options.bots_ips = open(interpolate_config(options.bots_ips, 'filterbots', 'bots_ips'), "r")
    options.ip_ua_re  = interpolate_config(options.ip_ua_re, 'filterbots', 'ip_ua_re')    
    options.reverse  = interpolate_config(options.reverse, 'filterbots', 'reverse', 
                                          default=False, type=bool)
    options.printlines  = interpolate_config(options.printlines, 'filterbots', 'printlines', 
                                             default=False, type=bool)    
    
    return options, args

def filterbots(options, args, fh):
    """Filter bots from a log stream using
    ip/useragent blacklists"""
    bots_ua = dict.fromkeys([l.strip() for l in options.bots_ua])
    bots_ips = dict.fromkeys([l.strip() for l in options.bots_ips])

    ua_ip_re = re.compile(options.ip_ua_re)

    num_lines=0
    num_filtered=0
    for line in imap(lambda x: x.strip(), fh):
        match = ua_ip_re.match(line)
        if not match:
            logging.warn("No match for line: %s", line)
            continue
    
        matchgroups = match.groupdict()

        if options.reverse ^ (matchgroups.get('ua', None) in bots_ua or \
           matchgroups.get('ip', None) in bots_ips):
            logging.debug("Filtering line: %s", line)
            num_filtered+=1
            continue

        num_lines+=1
        if options.printlines:
            print line

    logging.info("Number of lines after filtering: %s", num_lines)
    logging.info("Number of lines filtered: %s", num_filtered)

    return num_filtered, num_lines

def filterbots_main():
    """Console entry-point"""
    options, args = filterbots_parse_args()
    filterbots(options, args, fh=sys.stdin.readlines())
    return 0

