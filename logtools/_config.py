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
#
# ........................................ NOTICE
#
# This file has been derived and modified from a source licensed under Apache Version 2.0.
# See files NOTICE and README.md for more details.
#
# ........................................ ******

"""
logtools._config

Interpolation of logtools parameters using file-based configuration
in /etc/logtools.cfg or ~/.logtoolsrc.
"""

import os
import sys
import logging

from configparser import ConfigParser, NoOptionError, NoSectionError, ExtendedInterpolation

__all__ = ['logtools_config', 'interpolate_config', 'AttrDict', 'setLoglevel']

logtools_config = ConfigParser( interpolation = ExtendedInterpolation())
logtools_config_paths = ['/etc/logtools.cfg', os.path.expanduser('~/.logtoolsrc')]
logtools_config.read(logtools_config_paths)


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
    except KeyError as err:
        if False:
            #at this point, logging not intialized (?)
            logging.info( f"{err}\n\ttype parm={type}", file=sys.stderr)        
        raise KeyError("Invalid parameter type: '{0}'".format(type))    
    except (NoOptionError, NoSectionError) as err:
        if False:
            #at this point, logging not intialized (?)
            logging.info( f"Error: {err}\n\tdefault={default}"
                +f"\n\ttype parm={type}\n\tsection={repr(section)}\tkey={repr(key)}"
                +f"\n\tconfig file sought: {logtools_config_paths}")
        
        if default is not None:
            return default
        raise KeyError("Missing parameter: '{0}'".format(key))
    
    
def setLoglevel(options):
    """ Customize logging level, using options dictionnary collected from CLI
    """
    if options.logLevSym and options.logLevVal:
        print("Flags --sym and --num are exclusive", file = sys.stderr )
        sys.exit(1)
    try :
        basics  ={'format' : "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        if options.logLevVal:
            basics['level'] = options.logLevVal
        elif options.logLevSym:
            basics['level'] = options.logLevSym 
        logging.basicConfig(**basics)
        
    except ValueError as err:
        print( f"Bad --sym or --num flag value\n\t{err}", file = sys.stderr)
        sys.exit(2)
    except Exception as err:
        print( f"Unexpected error\n\t{err}", file = sys.stderr)
        raise

