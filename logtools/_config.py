#!/usr/bin/env python
"""
logtools._config

Interpolation of logtools parameters using file-based configuration
in /etc/logtools.cfg or ~/.logtoolsrc.
"""

import os
import sys
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError

__all__ = ['logtools_config', 'interpolate_config']

logtools_config = SafeConfigParser() 
logtools_config.read(['/etc/logtools.cfg', os.path.expanduser('~/.logtoolsrc')])

def interpolate_config(var, section, key):
    """Interpolate a parameter. if var is None,
    try extracting value from section.key in configuration file.
    If fails, can raise Exception / issue warning"""
    try:
        return var or logtools_config.get(section, key)
    except (NoOptionError, NoSectionError):
        raise KeyError("Missing parameter: '{0}'".format(key))
    

