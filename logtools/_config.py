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

__all__ = ['logtools_config', 'interpolate_config', 'AttrDict', 'setLoglevel' ]


if  "LOGTOOLS_RC" in os.environ and len(os.environ["LOGTOOLS_RC"]) > 0 :
    logtools_config_paths = list(map(os.path.expanduser,
                                     os.environ["LOGTOOLS_RC"].split(":")))
    s = "(from env. LOGTOOLS_RC)"
else:
    s = ""
    logtools_config_paths = ['/etc/logtools.cfg', os.path.expanduser('~/.logtoolsrc')]
logging.debug(f"INI (ConfigParser) files sought for {s}:{logtools_config_paths}")

logtools_config = ConfigParser( interpolation = ExtendedInterpolation())
logtools_config.read(logtools_config_paths)


MYSQL_NOT_FOUND = None


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

def setMysqlNotFound(x):
    """ Used to set MYSQL_NOT_FOUND from __init, permits checkMysql to warn when
        this DB interface is absent. This functionality will evolve since the
        plan is to be SQL interface neutral.....
    """
    global MYSQL_NOT_FOUND
    MYSQL_NOT_FOUND = x

def checkMysql(checkOptions, options, required=False):
    """ Used in functions that may use the DB interface either that this is required
        or that functionality may be degraded.

        <condition> = mysql is not used or pymysql is available 
        arguments: 
              options:  dictionnary, derived from command line args
              checkOptions: look for this entry ( *connect_string ) in options which
                            is a dictionnary, see if it names mysql
              required: if True and <condition> not met, then signal an error and exit
                        if False : no action  
                        if None   and <condition> not met: emit a warning
    """ 
    def usingMysql():
        if checkOptions in options:
            return options[checkOptions].startswith("mysql:")
        return False
        
    doExit=False
    if MYSQL_NOT_FOUND is not None:
         if MYSQL_NOT_FOUND:
             if  usingMysql():
                 if required: 
                     logging.error(f"Module pymysql not available")
                     doExit = True
                 elif required is None:
                     logging.warning(f"Module pymysql not available, functionality may be degraded")
         else:
             logging.debug(f"CheckMysql:_config.MYSQL_NOT_FOUND assigned:{MYSQL_NOT_FOUND}")
    else:
        logging.error(f"CheckMysql:_config.MYSQL_NOT_FOUND  not assigned")
        doExit = required
    if doExit:
        sys.exit(20)

def checkDpath(doExtended=True):
    """
    This checks that we are using a full featured (i.e. extended when compared with
    standard package distribution) dpath module, able to recognize segments with 're'
    regexps.

    The option is then set according to argument doExtended (default:True).

    Experimental method used since we do not control the releases of dpath.
    """
    import dpath

    if hasattr(dpath.options,"DPATH_ACCEPT_RE_REGEXP"):
        dpath.options.DPATH_ACCEPT_RE_REGEXP = doExtended
        return

    if not doExtended:
        return

    if ( 'dpath'  in logtools_config.sections()
         and logtools_config['dpath'].get('no-dpath-warning').lower()=="true"):
        return

    js={"Env":True, "Cmd":True}
    selPath = '{(Env|Cmd)}'
    x = dpath.util.search(js, selPath)

    if  len(x) != 2:
        wmsg="""\
    You are using a version of dpath which does not support 're' regexps style
    matching. Nested dict/json keys will be limited to bash globs. You may load a
    full featured dpath from  https://github.com/AlainLich/dpath-python.

    You can suppress this warning by adding key 'no-dpath-warning: True' in section 'dpath' of
    your configuration file '~/.logtoolsrc'.

    """
        logging.warn(wmsg)
