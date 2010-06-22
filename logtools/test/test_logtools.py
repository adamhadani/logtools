#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License. 
"""Unit-test code for logtools"""

import os
import sys
import unittest
import logging
from StringIO import StringIO

from logtools import filterbots, geoip
from logtools import logtools_config, interpolate_config

logging.basicConfig(level=logging.INFO)

class AttrDict(dict):
    """Helper class for simulation OptionParser options object"""
    def __getattr__(self, key):
        return self[key]


class ConfigurationTestCase(unittest.TestCase):
    def testInterpolation(self):
        self.assertEqual(1, interpolate_config(1, 'bogus_sec', 'bogus_key'))
        self.assertRaises(KeyError, interpolate_config, None, 'bogus_sec', 'bogus_key')


class FilterBotsTestCase(unittest.TestCase):
    def setUp(self):
        self.options = AttrDict()
        self.options.reverse = False
        self.options.printlines = False
        self.options.ip_ua_re = "^(?P<ip>.*?) - USER_AGENT:'(?P<ua>.*?)'"
        self.options.bots_ips = StringIO()
        self.options.bots_ua = StringIO(
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)\n"
        )

        self.fh = StringIO(
            "127.0.0.1 - USER_AGENT:'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' - ...\n" \
            "255.255.255.255 - USER_AGENT:'Mozilla' - ...\n"
        )

    def testFiltering(self):
        ret = filterbots(self.options, None, self.fh)
        self.assertEquals(ret, (1,1), "filterbots output different than expected: %s" % str(ret))


class GeoIPTestCase(unittest.TestCase):
    def setUp(self):
        self.options = AttrDict()
        self.options.ip_re = "^(.*?) -"
        
        self.fh = StringIO(
            "127.0.0.1 - USER_AGENT:'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)' - ...\n" \
            "255.255.255.255 - USER_AGENT:'Mozilla' - ...\n"
        )

    def testGeoIP(self):
        try:
            import GeoIP
        except ImportError:
            print >> sys.stderr, "GeoIP Python package not available - skipping geoip unittest."
            return

        ret = geoip(self.options, None, self.fh)


if __name__ == "__main__":
    unittest.main()
