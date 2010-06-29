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
logtools._geoip
GeoIP interoperability tool.
Requires the GeoIP library and Python bindings
"""
import os
import re
import sys
import logging
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['geoip_parse_args', 'geoip', 'geoip_main']

def geoip_parse_args():
    parser = OptionParser()
    parser.add_option("-r", "--re", dest="ip_re", default=None, 
                    help="Regular expression to lookup IP in logrow")
    parser.add_option("-p", "--print", dest="printline", default=None, action="store_true",
                    help="Print original log line with the geolocation. By default we only print <country, ip>")    

    parser.add_option("-P", "--profile", dest="profile", default='geoip',
                      help="Configuration profile (section in configuration file)")
    
    options, args = parser.parse_args()
    
    # Interpolate from configuration
    options.ip_re  = interpolate_config(options.ip_re, options.profile, 'ip_re')
    options.ip_re  = interpolate_config(options.printline, options.profile, 'print', 
                                        type=bool, default=False)

    return AttrDict(options.__dict__), args

def geoip(options, args, fh):
    try:
        import GeoIP
    except ImportError:
        logging.error("GeoIP Python package must be installed to use logtools geoip command")
        sys.exit(-1)

    gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    ip_re = re.compile(options.ip_re)

    for line in imap(lambda x: x.strip(), fh):
        match = ip_re.match(line)
        if match: 
            ip = match.group(1)
            geocode = gi.country_name_by_addr(ip)
            if geocode is None:
                logging.debug("No Geocode for IP: %s", ip)
            yield geocode, ip, line

def geoip_main():
    """Console entry-point"""
    options, args = geoip_parse_args()
    for geocode, ip, line in geoip(options, args, fh=sys.stdin.readlines()):
        if options.printline is True:
            print "{0}\t{1}".format(line, geocode)
        else:
            print "{0}\t{1}".format(ip, geocode)
    return 0
