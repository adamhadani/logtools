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
logtools._serve

Miniature web server for delivering real-time log stats
"""

import os
import re
import sys
import logging
import wsgiref
from itertools import imap
from random import randint
from operator import itemgetter
from optparse import OptionParser
from abc import ABCMeta, abstractmethod

from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['logserve_parse_args', 'logserve', 'logserve_main']

def logserve_parse_args():
    pass

def logserve(options, args, fh):
    pass

def logserve_main():
    """Console entry-point"""
    options, args = logserve_parse_args()
    logserve(options, args, fh=sys.stdin.readlines())
    return 0
