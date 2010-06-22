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
logtools.geoip
GeoIP interoperability tool.
Requires the GeoIP library and Python bindings
"""
import os
import re
import sys
import logging
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config

def geoip_parse_args():
    parser = OptionParser()
    parser.add_option("-r", "--re", dest="ip_re", default=None, 
                    help="Regular expression to lookup IP in logrow")

    options, args = parser.parse_args()
    
    # Interpolate from configuration
    options.ip_re  = interpolate_config(options.ip_re, 'geoip', 'ip_re')

    return options, args

def geoip():
    try:
        import GeoIP
    except ImportError:
        logging.error("GeoIP Python package must be installed to use logtools geoip command")
        sys.exit(-1)

    options, args = geoip_parse_args()
    gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    ip_re = re.compile(options.ip_re)

    for line in imap(lambda x: x.strip(), sys.stdin.readlines()):
        match = ip_re.match(line)
        if match: 
            ip = match.group(1)
            geocode = gi.country_name_by_addr(ip)
            if geocode is None:
                logging.debug("No Geocode for IP: %s", ip)
            print "{0}\t{1}".format(ip, geocode)


if __name__ == "__main__":
    sys.exit(main())

