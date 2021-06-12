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
logtools._flattenjson

Extract objects (dictionaries) from inside a JSON list.
Useful when piping into tools such as json2csv which expect
"flat" json streams.

"""
import sys
from json import dumps, load
from optparse import OptionParser

from ._config import interpolate_config, AttrDict


__all__ = ['flattenjson_parse_args', 'flattenjson', 'flattenjson_main']


def flattenjson_parse_args():
    parser = OptionParser()
    parser.add_option("-f", "--field", dest="field", default=None,
                      help="JSON root field to extract objects from (should point to a list)")  # noqa
    parser.add_option("-P", "--profile", dest="profile", default='flattenjson',
                      help="Configuration profile (section in configuration file)")  # noqa
    
    parser.add_option("-R", "--raw", dest="raw", default=None, action="store_true",
                      help="When set output is not encoded for UTF-8")  
                      ## default kept for compatibility
    
    options, args = parser.parse_args()
    options.field = interpolate_config(options.field, options.profile, 'field')
    options.raw = interpolate_config(options.raw, options.profile, 'raw')

    return AttrDict(options.__dict__), args


def flattenjson(options, args, fh):
    data = load(fh)

    try:
        for line in data[options.field]:
            yield dumps(line)
    except Exception as err:
        print(f"Error: ({type(err)}){err}", file=sys.stderr)
        print(f"\tkeys avail in data ({type(data)}): {data.keys()}", file=sys.stderr)
        raise err
    
def flattenjson_main():
    """Console entry-point"""
    options, args = flattenjson_parse_args()
    for row in flattenjson(options, args, fh=sys.stdin):
        if row:
            if options.raw:
                print(row)
            else:
                print( row.encode('utf-8', 'ignore') )
    return 0
