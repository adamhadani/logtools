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
# ........................................ COPYRIGHT
#
# (C) Alain Lichnewsky, 2021
#     https://github.com/AlainLich
# ........................................ ******
#

"""
logtools._db
Perform various database operations based on information collected in a logstream,
and possibly from other sources.
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
from ._join import jsonKeyExtract
from ._config import logtools_config, interpolate_config, AttrDict, setLoglevel
from ._config import checkDpath, checkMysql
from .utils import flatten, ucodeNorm, getObj
from .ext_db import DB_Tree_Maker, NestedTreeDbOperator
import dpath
import dpath.util

checkDpath()

__all__ = ['logdb_parse_args', 'logdb', 'logdb_main']

def logdb_parse_args():
    usage = "%prog  [tag option]*\n"
    parser = OptionParser(usage=usage + "\n" + logdb.__doc__ )

    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")

    # ........................................
    parser.add_option( "--frontend", dest="frontend",
                      help="Front end to use for analyzing the input")
    parser.add_option( "--fe-keys", dest="fe_keys", default=1,
                      help="Front end keys for selection in front end (if relevant)")

    parser.add_option( "--in", dest="inFileName",
                           help="Input file, if omitted stdin is used")


    # ........................................
    parser.add_option("-b", "--dbOperator", dest="dbOperator",
                      help="DbOperator to use for joining. Currently available dbOperators: 'sqlalchemy'")
    parser.add_option("-C", "--join-connect-string", dest="dbOp_connect_string",
                      help="Connection string (e.g sqlalchemy db URI)")

    parser.add_option("-f", "--field", dest="field",
                      help="Index of field to use as field to operate on")

    parser.add_option("-F", "--join-remote-fields", dest="dbOp_remote_fields",
                      help="Fields to operate on")

    parser.add_option("-N", "--join-remote-name", dest="dbOp_remote_name",
                      help="Name of resource to operate on (e.g file name, table name)")

    parser.add_option("-K", "--join-remote-key", dest="dbOp_remote_key",
                      help="Name of remote key field to join on (e.g table field, file column index)")

    parser.add_option("-P", "--profile", dest="profile", default='dbOp',
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

    options.dbOperator = interpolate_config(options.dbOperator, options.profile, 'dbOperator')
    options.frontend = interpolate_config(options.frontend, options.profile, 'frontend')

    options.dbOp_connect_string = interpolate_config(options.dbOp_connect_string, options.profile, 'dbOp_connect_string')
    options.dbOp_remote_fields = interpolate_config(options.dbOp_remote_fields, options.profile, 'dbOp_remote_fields')
    options.dbOp_remote_name = interpolate_config(options.dbOp_remote_name, options.profile, 'dbOp_remote_name')
    options.dbOp_remote_key = interpolate_config(options.dbOp_remote_key, options.profile, 'dbOp_remote_key')

    # Set the logging level
    setLoglevel(options)

    return AttrDict(options.__dict__), args


def logdb(fh, **options):
    """
Function: Perform misc. operations between new logstream  information and information
          in a database

   - front-end : option 'parser' will result filtering the input by indicated
                 front-end parser. Our code is close to logparse. It remains to be
                 seen if this is useful  or could be done using logparse.

   - dbOperator(s) take arguments from CL options or configuration file,
         db functions are selected by keyword dbOperator among available.


    Keyword arguments:
?          field:                field(s) to join from the input
?          keys:                 keys to be use in frontend
          delimiter:
          dbOperator:            back end to effect operations on data base
          frontend:             function returning iterator to filter incoming data
          fe_keys:              keys for selection in front end
          in:                   input file

          dbOp_connect_string:
          dbOp_remote_fields:
          dbOp_remote_name:
          dbOp_remote_key:

    If absent on the command line, keywords may be filled from ~/.logtoolsrc, section
    "dbOp" (may be overriden by flag -P)

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
        # Use a frontend parser to extract field to merge/sor
        frontend =  getObj(options.frontend, (logtools.parsers, logtools.parsers2))()

        if isinstance(frontend, logtools.parsers2.JSONParserPlus):
            extract_func = logtools.parsers2.dpath_getter_gen_mult(frontend, options.field,
                                                                   options)
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



    # dbOperator selection and parametrization
    tbl = {
        "SQLAlcDbOp": NestedTreeDbOperator,
    }
    try:
        dbOperator_impl = tbl[options.dbOperator](remote_fields=options.dbOp_remote_fields,
                                                  remote_name=options.dbOp_remote_name,
                                                  remote_key=options.dbOp_remote_key,
                                                  connect_string=options.dbOp_connect_string)
    except KeyError as err:
        print(f"{err}\nThe --dbOperator flag should point at an entry in:{tbl.keys()}",
              file=sys.stderr)
        sys.exit(2)
    except Exception as err:
        print(f"{err}\nError in connecting to the data base server", file=sys.stderr)
        sys.exit(2
        )

    #   See what happens, we probably need to check that the class has adequate parent(s)
    dbOperator_impl.createDeferredClasses( DB_Tree_Maker)
    dbOperator_impl.prepareDeferred()
        
    # perform the operation
    for row in map(extract_func, fh):
        if fe_returns_Json:
            value = jsonKeyExtract(row,field)
        else:
            value = row[field]
        for dbOp_row in dbOperator_impl.operate(field, value,row ):
            yield value, str(row) + " => " + delimiter + delimiter.join(map(str, dbOp_row))



def logdb_main():
    """Console entry-point"""
    options, args = logdb_parse_args()
    
    checkMysql(required=True)

    if options.inFileName:
        fh = open(options.inFileName, "r")
    else:
        fh= sys.stdin

    for key, row in logdb(fh=fh, *args,  **options):
        print( row, file = sys.stdout )

    if options.inFileName:
        fh.close()

    return 0
