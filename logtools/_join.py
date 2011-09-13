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
logtools._join

Perform a join between log stream and
some other arbitrary source of data.
Can be used with pluggable drivers e.g
to join against database, other files etc.
"""
import re
import sys
import logging
import unicodedata
from time import time
from itertools import imap
from datetime import datetime
from optparse import OptionParser
from urlparse import parse_qs, urlsplit

from logtools.join_backends import *
from _config import logtools_config, interpolate_config, AttrDict

__all__ = ['logjoin_parse_args', 'logjoin', 'logjoin_main']

def logjoin_parse_args():
    usage = "%prog " \
          "-f <field> " \
          "-d <delimiter_character> " \
          "-t <timestamp_format_string>"
    parser = OptionParser(usage=usage)
    
    parser.add_option("-f", "--field", dest="field", type=int,
                      help="Index of field to use as field to join on")
    parser.add_option("-d", "--delimiter", dest="delimiter",
                      help="Delimiter character for field-separation")
    parser.add_option("-b", "--backend", dest="backend",  
                      help="Backend to use for joining. Currently available backends: 'sqlalchemy'")
    
    parser.add_option("-C", "--join-connect-string", dest="join_connect_string",
                      help="Connection string (e.g sqlalchemy db URI)")
    parser.add_option("-F", "--join-remote-fields", dest="join_remote_fields",
                      help="Fields to include from right join clause")        
    parser.add_option("-N", "--join-remote-name", dest="join_remote_name",
                      help="Name of resource to join to (e.g file name, table name)")        
    parser.add_option("-K", "--join-remote-key", dest="join_remote_key",
                      help="Name of remote key field to join on (e.g table field, file column index)")        
    
    parser.add_option("-P", "--profile", dest="profile", default='qps',
                      help="Configuration profile (section in configuration file)")

    options, args = parser.parse_args()

    # Interpolate from configuration
    options.field  = interpolate_config(options.field, options.profile, 'field', type=int)
    options.delimiter = interpolate_config(options.delimiter, options.profile, 'delimiter', default=' ')
    options.backend = interpolate_config(options.backend, options.profile, 'backend')
    
    options.join_connect_string = interpolate_config(options.join_connect_string, options.profile, 'join_connect_string')
    options.join_remote_fields = interpolate_config(options.join_remote_fields, options.profile, 'join_remote_fields')
    options.join_remote_name = interpolate_config(options.join_remote_name, options.profile, 'join_remote_name')
    options.join_remote_key = interpolate_config(options.join_remote_key, options.profile, 'join_remote_key')

    return AttrDict(options.__dict__), args


def logjoin(fh, field, delimiter, backend, join_connect_string, 
            join_remote_fields, join_remote_name, join_remote_key, **kwargs):
    """Perform a join"""
    
    field = field-1
    delimiter = unicode(delimiter)
    
    backend_impl = {
        "sqlalchemy": SQLAlchemyJoinBackend
    }[backend](remote_fields=join_remote_fields, remote_name=join_remote_name, 
                       remote_key=join_remote_key, connect_string=join_connect_string)
    
    for row in imap(lambda x: x.strip(), fh):
        key = row.split(delimiter)[field]
        for join_row in backend_impl.join(key):
            yield key, unicode(row) + delimiter + delimiter.join(imap(unicode, join_row))

def logjoin_main():
    """Console entry-point"""
    options, args = logjoin_parse_args()
    for key, row in logjoin(fh=sys.stdin, *args, **options):
        print >> sys.stdout, unicodedata.normalize('NFKD', unicode(row))\
              .encode('ascii','ignore')

    return 0
