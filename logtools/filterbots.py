#!/usr/bin/env python
"""
filterbots
Filter bots from logrows based on an ip/host and useragent blacklists.

"""
import re
import sys
import logging
from itertools import imap
from optparse import OptionParser

from _config import logtools_config, interpolate_config

def parse_args():
    parser = OptionParser(usage="%prog -u <useragents_blacklist_file> -i <ips_blacklist_file> -r <ip_useragent_regexp>")
    parser.add_option("-u", dest="bots_ua", default=None, help="Bots useragents blacklist file")
    parser.add_option("-i", dest="bots_ips", default=None, help="Bots ips blacklist file")
    parser.add_option("-r", dest="ip_ua_re", default=None, 
                        help="Regular expression to match IP and useragent field. Should have a 'ip' and 'ua' named groups")
    parser.add_option("-p", "--print", dest="printlines", action="store_true", default=False, 
                        help="Print non-filtered lines")
    parser.add_option("-R", "--reverse", dest="reverse", action="store_true", default=False, help="Reverse filtering")

    options, args = parser.parse_args()

    # Interpolate from configuration
    options.bots_ua  = interpolate_config(options.bots_ua, 'filterbots', 'bots_ua')
    options.bots_ips = interpolate_config(options.bots_ips, 'filterbots', 'bots_ips')
    options.ip_ua_re  = interpolate_config(options.ip_ua_re, 'filterbots', 'ip_ua_re')
    
    return options, args

def filterbots():
    options, args = parse_args()
    bots_ua = dict.fromkeys([l.strip() for l in open(options.bots_ua, "r")])
    bots_ips = dict.fromkeys([l.strip() for l in open(options.bots_ips, "r")])

    ua_ip_re = re.compile(options.ip_ua_re)

    num_lines=0
    num_filtered=0
    for line in imap(lambda x: x.strip(), sys.stdin.readlines()):
        match = ua_ip_re.match(line)
        if not match:
            logging.warn("No match for line: %s", line)
            continue

        matchgroups = match.groupdict()
        if options.reverse ^ (matchgroups['ua'] in bots_ua or \
           matchgroups['ip'] in bots_ips):
            logging.debug("Filtering line: %s", line)
            num_filtered+=1
            continue

        num_lines+=1
        if options.printlines:
            print line

    print >> sys.stderr, "Number of lines after filtering: ", num_lines
    print >> sys.stderr, "Number of lines filtered: ", num_filtered

if __name__ == "__main__":
    sys.exit(main())
