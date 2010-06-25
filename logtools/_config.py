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
logtools._config

Interpolation of logtools parameters using file-based configuration
in /etc/logtools.cfg or ~/.logtoolsrc.
"""

import os
import sys
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError

__all__ = ['logtools_config', 'interpolate_config', 'AttrDict']

logtools_config = SafeConfigParser() 
logtools_config.read(['/etc/logtools.cfg', os.path.expanduser('~/.logtoolsrc')])


class AttrDict(dict):
    """Helper class for simulation OptionParser options object"""
    def __getattr__(self, key):
        return self[key]

def interpolate_config(var, section, key, default=None, type=str):
    """Interpolate a parameter. if var is None,
    try extracting value from section.key in configuration file.
    If fails, can raise Exception / issue warning"""
    try:
        return var or {
            str: logtools_config.get,
            bool: logtools_config.getboolean,
            int:  logtools_config.getint,
            float: logtools_config.getfloat
        }.get(type, str)(section, key)
    except KeyError:
        raise KeyError("Invalid parameter type: '{0}'".format(type))    
    except (NoOptionError, NoSectionError):
        if default is not None:
            return default
        raise KeyError("Missing parameter: '{0}'".format(key))
    
    

