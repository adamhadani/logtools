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

from logtools import filterbots, geoip, logtools_config, interpolate_config

class ConfigurationTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def testConfiguration(self):
        self.assertRaises(KeyError, interpolate_config, None, 'bogus_sec', 'bogus_key')

class FilterBotsTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def testFilterBots(self):
        pass

class GeoIPTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def testGeoIP(self):
        pass
if __name__ == "__main__":
    unittest.main()
