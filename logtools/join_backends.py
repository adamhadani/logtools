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
logtools.join_backends
Backends used by the logjoin API / tool
"""
import os
import re
import sys
import logging
from functools import partial
from datetime import datetime
from abc import ABCMeta, abstractmethod

import json
from sqlalchemy import create_engine

from ._config import AttrDict

__all__ = ['JoinBackend', 'SQLAlchemyJoinBackend']


class JoinBackend(object):
    """Base class for all our parsers"""
    __metaclass__ = ABCMeta

    def __init__(self, remote_fields, remote_name, 
                 remote_key, connect_str=None):
        """Initialize. Can get an optional connection
        string"""
        
    @abstractmethod
    def join(self, rows):
        """Implement a join generator"""
        
        
class SQLAlchemyJoinBackend(JoinBackend):
    """sqlalchemy-based join backend,
    allowing for arbitrary DB's based on a
    connection URL"""
    
    def __init__(self, remote_fields, remote_name, 
                 remote_key, connect_string):
        """Initialize db connection"""
        self.connect_string = connect_string
        self.remote_fields = remote_fields
        self.remote_name = remote_name
        self.remote_key = remote_key
        self.query_stmt = self._create_query_stmt()

        self.connect()
        
    def _emitDiagnostic(self, msg, err):
        p = { "connect":self.connect_string,
                  "remote_flds":self.remote_fields,
                  "remote_name":self.remote_name, 
                  "remote_key":self.remote_key,
                  "query":self.query_stmt
                }
        pstr= "\n\t".join( f"{k:20}\t{v}"  for (k,v) in p.items() )
        print(f"Error: {msg}\n\t{err}\n\t{pstr}", file=sys.stderr)
        
    def connect(self):
        """Connect to remote join backend (DB)"""
        try:
            self.db = create_engine(self.connect_string)
        except Exception as err:
            self._emitDiagnostic( "connect to DB server", err)
            raise err
        
    def join(self, key):
        engine = self.db
        try:
            with engine.connect() as connection:
                result = connection.execute(self.query_stmt, key=key)
                for row in result:
                    yield row
        except Exception as err:
            self._emitDiagnostic( "In engine.connect or in connection.execute\n\t"
                                  +f"SQL={self.query_stmt}\n\tkey={key} ",  err)
            raise err
        
                
    def _create_query_stmt(self):
        """Create valid query statement string
        to be used with interpolating bound variables.
        Unfortunately, there is inconcistency in syntax
        across different drivers"""
        connstr = self.connect_string


        #
        # Generalize by authorizing removing the WHERE clause; likely a
        # more general mechanism will be inserted to add to the SQL stmt
        # or a more general mechanism to emit the SQL
        #
        if self.remote_key != "-":
            if connstr.startswith("sqlite"):
                query_stmt2 = """WHERE {0} = :key""".format(self.remote_key)            
            else:
                query_stmt2 = """WHERE {0} = %(key)s""".format(self.remote_key)
        else:
            query_stmt2 = ""
            
        query_stmt1 =  """SELECT {0} FROM {1} """.format(self.remote_fields, 
                                        self.remote_name)

            
        return query_stmt1 + query_stmt2
