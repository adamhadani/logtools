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
# ........................................ NOTICE
#
# This file has been derived and modified from a source licensed under Apache Version 2.0.
# See files NOTICE and README.md for more details.
#
# ........................................ ******

"""
logtools.utils
A few programmatic utilities / methods.
These are not exposed as command-line tools
but can be used by other methods
"""

import os
import sys
import time
import unicodedata
from types import ModuleType

	
def tail_f(fname, block=True, sleep=1):
	"""Mimic tail -f functionality on file descriptor.
	This assumes file current position is already where
	we want it (i.e seeked to end).
	
	This code is mostly adapted from the following Python Recipe:
	http://code.activestate.com/recipes/157035-tail-f-in-python/
	"""
	fh = open(fname, 'r')
	
	while 1:
		where = fh.tell()
		line = fh.readline()
		if not line:
			if block:
				time.sleep(sleep)
			else:
				yield
			fh.seek(where)
		else:
			yield line


# ................................................................................
#
#  Programming utilities
#
# ................................................................................
def flatten(l):
    """\
recursively flatten list given in argument
    """
    if l == []:
        return l
    if isinstance(l[0], list):
        return flatten(l[0]) + flatten(l[1:])
    return l[:1] + flatten(l[1:])

# unicodedata — Unicode Database
# This module provides access to the Unicode Character Database (UCD) which defines
# character properties for all Unicode characters.
# - unicodedata.normalize(form, unistr)
#               Return the normal form form for the Unicode string unistr.
#               Valid values for form are ‘NFC’, ‘NFKC’, ‘NFD’, and ‘NFKD’.

def ucodeNorm(x, form='NFKD'):
    """
 1) ensure x is a string
 2) unicode normalize it
 3) encode for ascii thus getting a byte string
    """
    return unicodedata.normalize(form, str(x)).encode('ascii','ignore')


def getObj(fname, modules):
    """ Get an object from an iterable of modules ; used to avoid using 'eval' which
        is susceptible to code injection and probably slower. 
        Argument : name of the object to retrieve
                   modules: iterable returning modules
    """    
    for m in modules:
        if not isinstance(m, ModuleType):
            raise RuntimeError(f"Wrong type {type(m)}for {m}, should be 'module'")    
        vm =vars(m)
        if fname in vm:
           return vm[fname]
    raise RuntimeError(f"object named '{fname}' not found in modules")
