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
logtools._join

Perform a join between log stream and
some other arbitrary source of data.
Can be used with pluggable drivers e.g
to join against database, other files etc.
"""
import re
import sys
import logging
from time import time
from datetime import datetime
from optparse import OptionParser
from urllib.parse import parse_qs, urlsplit
from functools import partial, reduce
from operator import and_

import logtools.parsers
import logtools.parsers2
from .join_backends import *
from ._config import logtools_config, interpolate_config, AttrDict, setLoglevel
from ._config import checkDpath, checkMysql
from .utils import flatten, ucodeNorm, getObj

import dpath
import dpath.util

checkDpath()

__all__ = ['logjoin_parse_args', 'logjoin', 'logjoin_main']

def jsonKeyExtract(jsonIn,selector):
    """\
Extract values that correspond to selector from a list of dict in json
form. The result is flattened recursively.
    """
    ret =  flatten(dpath.util.values(jsonIn, selector))
    logging.debug(f"In jsonKeyExtract:\n\tjsonIn={jsonIn}\n\tselector={selector}" +
                  f"\n\treturning:\t{ret}" )

    return ret

def logjoin_parse_args():
    usage = "%prog  [tag option]*\n"
    parser = OptionParser(usage=usage + "\n"+ logjoin.__doc__)

    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")

    # ........................................
    parser.add_option( "--frontend", dest="frontend",
                      help="Front end to use for analyzing the input")
    parser.add_option( "--fe-keys", dest="fe_keys", default=1,
                      help="Front end keys for selection in front end (if relevant)")

    parser.add_option( "--in", dest="inFileName",
                           help="Input file, if omitted stdin is used")

    parser.add_option( "--out-encoding", dest="output_encoding",
                           help="Encoding for output; accepted values: 'None' "
                                + " '' or ‘NFKD’: (backwards compat)"
    )

    # ........................................
    parser.add_option("-b", "--backend", dest="backend",
                      help="Backend to use for joining. Currently available backends: 'sqlalchemy'")
    parser.add_option("-f", "--field", dest="field",
                      help="Index of field to use as field to join on")
    parser.add_option("-C", "--join-connect-string", dest="join_connect_string",
                      help="Connection string (e.g sqlalchemy db URI)")
    parser.add_option("-F", "--join-remote-fields", dest="join_remote_fields",
                      help="Fields to include from right join clause")
    parser.add_option("-N", "--join-remote-name", dest="join_remote_name",
                      help="Name of resource to join to (e.g file name, table name)")
    parser.add_option("-K", "--join-remote-key", dest="join_remote_key",
                      help="Name of remote key field to join on (e.g table field, file column index)")

    parser.add_option("-P", "--profile", dest="profile", default='logjoin',
                      help="Configuration profile (section in configuration file)")

    # logging level for debug and other information
    parser.add_option("-s","--sym" , type = str,
                                  dest="logLevSym",
                                  help="logging level (symbol)")

    parser.add_option("-n","--num" , type=int ,
                                  dest="logLevVal",
                                  help="logging level (value)")


    options, args = parser.parse_args()

    # Interpolate from configuration
    options.field  = interpolate_config(options.field, options.profile, 'field')
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter', default=' ')

    options.backend = interpolate_config(options.backend, options.profile, 'backend')
    options.output_encoding = interpolate_config(options.output_encoding, options.profile,
                                                'output_encoding')

    options.frontend = interpolate_config(options.frontend, options.profile, 'frontend')

    options.join_connect_string = interpolate_config(options.join_connect_string, options.profile, 'join_connect_string')
    options.join_remote_fields = interpolate_config(options.join_remote_fields, options.profile, 'join_remote_fields')
    options.join_remote_name = interpolate_config(options.join_remote_name, options.profile, 'join_remote_name')
    options.join_remote_key = interpolate_config(options.join_remote_key, options.profile, 'join_remote_key')

    # Set the logging level
    setLoglevel(options)

    return AttrDict(options.__dict__), args


def logjoin(fh, **options):
    """
Function: Perform a join between new information and information in a database
          table
   - front-end : option 'parser' will result filtering the input by indicated
                 front-end parser. Our code is close to logparse. It remains to be
                 seen if this is useful  or could be done using logparse.

   - backend(s) take arguments from CL options or configuration file,
         this will depend on the backends available
         + SQLAlchemyJoinBackend :

    Keyword arguments:
          field:                field(s) to join from the input
          keys:                 keys to be use in frontend
          delimiter:
          backend:
          frontend:             function returning iterator to filter incoming data
          join_connect_string:
          join_remote_fields:
          join_remote_name:
          join_remote_key:

    If absent on the command line, keywords may be filled from ~/.logtoolsrc, section
    "logjoin" (may be overriden by flag -P)
"""
    options=AttrDict(options)

    if isinstance(options.field, int) or \
       (isinstance(options.field, str) and options.field.isdigit()):
        # Field given as integer (index)
        field = int(options.field) - 1
    else:
        field = options.field

    delimiter = str(options.delimiter)
    fe_returns_Json = False
    # front end selection and parametrization
    if options.get('frontend', None):
        # Use a frontend parser to extract field to merge/sort
        frontend =  getObj(options.frontend, (logtools.parsers, logtools.parsers2))()
        if isinstance(frontend, logtools.parsers2.JSONParserPlus):
            extract_func = logtools.parsers2.dpath_getter_gen(frontend, options.field,
                                                              options.keys)
            fe_returns_Json =  frontend.fe_returns_Json()
        else:
            # Field given as string
            # Check how many fields are requested
            keys = options.field.split(",")
            L = len(keys)
            if L == 1:
                extract_func = lambda x: frontend(x.strip())[field]
            else:
                raise NotImplementedError("Multiple keys in frontend:{options.field}")

    else:
        # No frontend parser given, use indexed field based extraction
        keys = options.field.split(",")
        L = len(keys)
        if L == 1:
            extract_func = lambda x: x.strip().split(delimiter)[field]
        else:
            # Multiple fields requested
            is_indices = reduce(and_, (k.isdigit() for k in keys), True)
            exel_func = lambda x: x.strip().split(delimiter)[field]
            extract_func = logtools.parsers.multikey_getter_gen(exel_func, keys,
                                                                is_indices=is_indices)



    # backend selection and parametrization
    backend_impl = {
        "sqlalchemy": SQLAlchemyJoinBackend,
        "sqlalchemyV0": SQLAlchemyJoinBackendV0    # keep the non ORM version (Base class! )
    }[options.backend](remote_fields=options.join_remote_fields,
                       remote_name=options.join_remote_name,
                       remote_key=options.join_remote_key,
                       connect_string=options.join_connect_string)


    # perform the join
    for row in map(extract_func, fh):
        if fe_returns_Json:
            key = jsonKeyExtract(row,field)
        else:
            key = row[field]
        for join_row in backend_impl.join(key):
            yield key, str(row) + " => " + delimiter + delimiter.join(map(str, join_row))



def logjoin_main():
    """Console entry-point"""

    options, args = logjoin_parse_args()
    checkMysql(checkOptions="logjoin_connect_string", options=options, required=True)

    if options.inFileName:
        fh = open(options.inFileName, "r")
    else:
        fh= sys.stdin

    logging.info(f"options.output_encoding=({type(options.output_encoding)})'{options.output_encoding}'")
    if options.output_encoding is not None and options.output_encoding.lower() != 'none':
        if options.output_encoding == 'NFKD' or  options.output_encoding=='':
            trFn =  ucodeNorm
        else:
           raise NotImplementedError(f"--out-encoding, value {options.output_encoding}" +
                                      " not accepted")
    else:
        trFn =  lambda x:x

    for key, row in logjoin(fh=fh, *args,  **options):
        print( trFn(row), file = sys.stdout )

    if options.inFileName:
        fh.close()

    return 0
