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

from _config import AttrDict

from sqlalchemy.ext.sqlsoup import SqlSoup

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
                
        
    def connect(self):
        """Connect to remote join backend (DB)"""
        self.db = SqlSoup(self.connect_string)
        
        
    def join(self, key):
        rp = self.db.bind.execute(self.query_stmt, key=key)
        for row in rp.fetchall():
            yield row # dict(zip(field_names, row))
                
                
    def _create_query_stmt(self):
        """Create valid query statement string
        to be used with interpolating bound variables.
        Unfortunately, there is inconcistency in syntax
        across different drivers"""
        connstr = self.connect_string
        if connstr.startswith("sqlite"):
            query_stmt = """SELECT {0} FROM {1} WHERE {2} = :key""".format(self.remote_fields, 
                                                self.remote_name, self.remote_key)            
        else:
            query_stmt = """SELECT {0} FROM {1} WHERE {2} = %(key)s""".format(self.remote_fields, 
                                        self.remote_name, self.remote_key)
        
        return query_stmt
