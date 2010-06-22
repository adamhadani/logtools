#!/usr/bin/env python

import os
import re
import sys
import logging
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config

try:
    import GeoIP
except ImportError:
    logging.warn("GeoIP Python package must be installed to use logtools geoip command")

def parse_args():
    parser = OptionParser()
    parser.add_option("-r", "--re", dest="ip_re", default=None, 
                    help="Regular expression to lookup IP in logrow")

    options, args = parser.parse_args()
    
    # Interpolate from configuration
    options.ip_re  = interpolate_config(options.re, 'geoip', 'ip_re')

    if options.re is None:
        parser.error("Must supply IP regular expressions. Type --help for usage instructions")

    return options, args

def main():
    options, args = parse_args()
    gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)
    ip_re = re.compile(options.re)

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

