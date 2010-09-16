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
logtools.utils
A few programmatic utilities / methods.
These are not exposed as command-line tools
but can be used by other methods
"""

import os
import sys
import time
	
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
