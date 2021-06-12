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
logtools.join_backends
Backends used by the logjoin and db API / tool
"""
import os
import re
import sys
import logging
from functools import partial
from datetime import datetime
from abc import ABCMeta, abstractmethod
from collections import Iterable
import json

from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import Session, registry
from sqlalchemy.orm import declarative_base

from sqlalchemy.sql import text

from sqlalchemy.ext.declarative import DeferredReflection #support deferred reflection


# Apparently here we may encounter a SQLAlchemy version in transition to the ORM i/f ++
try:
    from sqlalchemy.orm import select
except Exception:
    from sqlalchemy.sql import select
# END ORM transition ............................................................... ++



Base = declarative_base()  # used for "mapped classes",
                           # see SQLAlchemyJoinBackend._create_table_query


from ._config import AttrDict

__all__ = [ 'SQLAlchemyJoinBackend', 'SQLAlchemyJoinBackendV0', "SQLAlchemyDbOperator"]
          # decided not to publicize the abstract Base classes, see PEP 8

def printMetadataTables(md, file=sys.stderr, sep1="\t->\t", sep2="\n\t"):
    """ Format the information in Metadata concerning tables,
        sep1 is the inner separator, sep2 the outer. If file is None, nothing
        gets printed and a string is returned.

    """
    l = ( f"{k}{sep1}({type(v)}):{repr(v)}" for (k,v) in md.tables.items() )
    if file is None:
       return sep2.join(l)
    print(sep2.join(l), file=file)

class JoinBackend():
    """Base class for all our parsers"""
    __metaclass__ = ABCMeta

    def __init__(self, remote_fields, remote_name,
                 remote_key, connect_str=None):
        """Initialize. Can get an optional connection
        string"""

    @abstractmethod
    def join(self, rows):
        """Implement a join generator"""
        raise RuntimeError("This base class method is abstract!")
              # why did the decorator not block this ???

class SQLAlchemyBackBase(JoinBackend):
    """sqlalchemy-based join backend, allowing for arbitrary DB's based on a
    connection URL"""
    __metaclass__ = ABCMeta

    def __init__(self, remote_fields, remote_name,
                 remote_key, connect_string):
        """Initialize db connection"""
        self.connect_string = connect_string
        self.remote_fields = remote_fields
        self.remote_name = remote_name
        self.remote_key = remote_key
        self.query_stmt_selector = None
        self.connection = None

        self.connect()

        # we postpone creating the queries after connect
        # since some of these may require introspection
        self.query_stmt_dict = self._create_query_stmts()


    def _emitDiagnostic(self, msg, err):
        p = { "connect":self.connect_string,
                  "remote_flds":self.remote_fields,
                  "remote_name":self.remote_name,
                  "remote_key":self.remote_key,
                  "query selector":self.query_stmt_selector,
                  "query": self.query_stmt_dict[self.query_stmt_selector]
                }
        pstr= "\n\t".join( f"{k:20}\t{v}"  for (k,v) in p.items() )
        print(f"Error: {msg}\n\t{err}\n\t{pstr}", file=sys.stderr)


class SQLAlchemyJoinBackendV0(SQLAlchemyBackBase):
    """sqlalchemy-based join backend,  allowing for arbitrary DB's based on a
    connection URL, using non ORM connection and lower level functions"""

    def __init__(self, remote_fields, remote_name,
                 remote_key, connect_string):
        self.metadata= Base.metadata

        SQLAlchemyBackBase.__init__(self, remote_fields, remote_name,
                 remote_key, connect_string)



    def connect(self):
        """Connect to remote join backend (DB); look at SQLAlch documentation
           regarding commits (Here we are reading only, so there is no issue).
        """
        try:
            self.db = create_engine(self.connect_string)
            self.connection =  self.db.engine.connect()
        except Exception as err:
            self._emitDiagnostic( "connect to DB server", err)
            raise err

    def __del__(self):
        if self.connection is not None:
            self.connection.close()

    def commit(self):
        if self.connection is not None:
            self.connection.commit()
        else:
            raise RuntimeError("Attempt to commit with a not open connection")

    def join(self, key):
        """ Perform the join query.
        """
        def yield_rows(key, doWhere=True):
            """ yield the table rows, where key is a single entry
            """
            if doWhere: 
               query = self.query_stmt_dict["wherekey"]
               args = {'selvalue' : key}
            else:
               query = self.query_stmt_dict[None]
               args = {}
               
            
            logging.debug(f"In {type(self)}.join.yield_rows query:\n\t{query}\n\tkey:{key}")
            result = self.connection.execute( text(query), key=key)
            
            logging.debug(f"In {type(self)}.join.yield_rows result returned from execute:{type(result)}{result}")

            for row in result:
                yield row
        
        engine = self.db
        
        try:
            if len(key) == 1:
                for r in yield_rows(key, len(key) > 0):
                    yield r
            else:
                for k in key:
                    ## Here must deal with situation where key is an array with len > 1
                    ## simplest way seems to be iterating.
                    for r in yield_rows(k, True):
                        yield r
            
        except Exception as err:
            self._emitDiagnostic( "In engine.connect or in connection.execute\n\t"
                                  +f"SQL={query_stmt}\n\tkey={key} ",  err)
            raise err



    def _create_query_stmts(self):
        """returns a dictionary of query formats, where the key designates the
           format, the value is a tuple, where the first elt is the builder function
           and the rest are its parameters
        """
        _C = SQLAlchemyJoinBackendV0._query_creators
        return { k: _C[k][0](self, *_C[k][1:]) for k in _C}


    def _create_query_stmt(self, where=True):
        """Create valid query statement string
        to be used with interpolating bound variables.
        Unfortunately, there is inconsistency in syntax
        across different drivers"""
        connstr = self.connect_string


        #
        # Generalize by authorizing removing the WHERE clause;
        # Use SQLAlchemy capability to handle various DBs with identical syntax
        if not isinstance(self.remote_key, str) and len(self.remote_key)!=1:
            where = False
            logging.error(f"class {type(self)} not appropriate for multivalued keys"
                          + f"\n\tkeys={self.remote_key}"
                          + f"\n\tdo not use --backend sqlalchemyV0"
            )
        if self.remote_key != "-" and where:
            query_stmt2 = """WHERE {0} = :key""".format(self.remote_key)
        else:
            query_stmt2 = ""

        query_stmt1 =  """SELECT {0} FROM {1} """.format(self.remote_fields,
                                        self.remote_name)


        return query_stmt1 + query_stmt2


    _query_creators= {
        None:       (_create_query_stmt, False),
       "wherekey": (_create_query_stmt, True),
       }


class SQLAlchemyORMBackBase(SQLAlchemyBackBase):
    """ Base class for SQLalchemy ORM using classes
        - via connect method: obtain database metadata by introspection on 
          the connected database
    """
    def __init__(self, remote_fields, remote_name, remote_key, connect_string):
                                      # for SQLAlch ORM, required for BASE.__init__
        self.metadata= Base.metadata
        self.session = None        # forSQLAlch Session
        self.reflectedBase = None  # for using  DeferredReflection 
        self.reflectedDict= {}  # for using  DeferredReflection 
          # see https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html
          
        SQLAlchemyBackBase.__init__(self, remote_fields, remote_name,
                                             remote_key, connect_string)
    def connect(self):
        """Connect to remote join backend (DB); look at SQLAlch documentation
           regarding commits (Here we are reading only, so there is no issue).
        """
        try:
            self.db = create_engine(self.connect_string)
            self.session =  Session(self.db.engine)
        except Exception as err:
            self._emitDiagnostic( "connect to DB server", err)
            raise err

        # load metadata from the actual database
        self.metadata.reflect(bind=self.db.engine)
        logging.debug(printMetadataTables(self.metadata, file=None))

    def __del__(self):
        if self.session is not None:
            self.session.close()

    # ................................................................................
    # Provide tools for using Deferred Reflection 
    # see https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html
            
    def getReflectedBase(self):
        """ 
          return class Reflected and Base to enable deferred reflection class creation
        """
        if self.reflectedBase is None:
            class Reflected(DeferredReflection):
                __abstract__ = True

            self.reflectedBase = Reflected    
        return (self.reflectedBase, Base)

    def registerReflected(self, clName, cl):
        """ register class that will need preparation, to be effected by method
            prepareDeferred
        """
        self.reflectedDict[clName]=cl

    def prepareDeferred(self):
        for (clNm,cl) in self.reflectedDict.items():
            logging.debug(f"about to prepare for class '{clNm}':{cl}")
            cl.prepare(self.db.engine)
    # ................................................................................

        
    def commit(self):
        if self.session is not None:
            self.session.commit()
        else:
            raise RuntimeError("Attempt to commit with a not open session")

    def _create_table_query(self,*args, **kwargs):
        """ Create a SQLAlchemy structure thus creating the Tables if needed
            from declarative  "Mapped Classes"
        """
        logging.debug(f"In {type(self)}.__create_table_query, args={args}, kwargs={kwargs}"
              +f"\ttable-base-name={self.remote_name}")


        engine = self.db
        self.metadata.create_all(engine)
        logging.debug( f"self.metadata after create_all: {repr(self.metadata)} "
                      +f"\n.tables=\n\t{printMetadataTables(self.metadata, file=None)}")

    def __repr__(self):
        return ( f"User(id={self.id!r}, name={self.user_id!r}, " +
                 f"application={self.application!r})" )



class SQLAlchemyJoinBackend(SQLAlchemyORMBackBase):
    """ sqlalchemy-based join backend, allowing for arbitrary DB's based on a connection
        URL.

        Focus: use SQLAlchemy higher level tools (ORM) for query creation, right now
               reproducing  the same effect as the base class. Then we will see....
    """
    def __init__(self, remote_fields, remote_name, remote_key, connect_string):

        SQLAlchemyORMBackBase.__init__(self, remote_fields, remote_name,
                                             remote_key, connect_string)

    def join(self, key):
        """ perform the join query/queries dependinf on key:
            - if key is empty list: remove WHERE Clause
            -        has len >= 1: iterate over key elements using WHERE

            TBD: see if we wouldn't prefer a general query execution method
            (not limited to join)
        """
        def yield_rows(key, doWhere=True):
            """ yield the table rows, where key is a single entry
            """
            if doWhere: 
               query = self.query_stmt_dict["wherekey"]
               args = {'selvalue' : key}
            else:
               query = self.query_stmt_dict[None]
               args = {}
               
            q = query(metadata=self.metadata, **args)
            logging.debug(f"In  {type(self)}.join.yield_rows query:\n\t{q}\n\tkey:{key}")
            result = self.session.execute(q)
            logging.debug(f"In {type(self)}.join.yield_rows result returned from execute:{type(result)}{result}")

            for row in result:
                yield row

        try:
            if len(key) == 1:
                for r in yield_rows(key, len(key) > 0):
                    yield r
            else:
                for k in key:
                    ## Here must deal with situation where key is an array with len > 1
                    ## simplest way seems to be iterating.
                    for r in yield_rows(k, True):
                        yield r

        except Exception as err:
            printMetadataTables(self.metadata)
            self._emitDiagnostic( "In session.execute(?)\n\t"
                                  +f"query={query}\n\tkey={key} "
                                  +f"\n\tSQL:{q}",  err)
            raise err


    def _create_query_stmts(self):
        """returns a dictionary of query formats, where the key designates the
           format, the value is a tuple, where the first elt is the builder function
           and the rest are its parameters
        """
        _C = SQLAlchemyJoinBackend._query_creators
        return { k: _C[k][0](self, *_C[k][1:]) for k in _C}


    def _create_query_stmt(self, where=True, **kwargs):
        raise RuntimeError(f"This base class method is not avail in {type(self)}")


    def _create_query(self,*args, **kwargs):
        """ Create a SQLAlchemy structure describing the query
        """
        # Return a callable, in the form of an object providing for internal state
        class query_select_fn():
            def __init__(self, tableName, remote_key, remote_fields):
               self.tableName = tableName
               self.remote_key = remote_key
               self.remote_fields= remote_fields

            def __call__(self, selvalue=None, metadata=None):
                table = Table(self.tableName, metadata)
                selkey= self.remote_key
                flds = text(self.remote_fields)

                if self.remote_key != "-":
                    rows = select(flds).select_from(table) \
                                       .filter(table.c[selkey] == selvalue)
                else:
                    rows = select(flds).select_from(table)

                logging.debug(f"{type(self)}.__call__\treturning rows:{type(rows)}{rows}")
                return rows

        return query_select_fn(self.remote_name, self.remote_key, self.remote_fields)



    _query_creators= {
       None:        (_create_query, False),
       "wherekey":  (_create_query, True),
       "createtbl": (SQLAlchemyORMBackBase._create_table_query, ),
                    # this creates all tables corresponding
                    # to mapped classes
       }


class SQLAlchemyDbOperator(SQLAlchemyORMBackBase):
    """ sqlalchemy-based database operator,
          - allowing for arbitrary DB's, inherits loading of metadata, 
            associates to the database using a connection URL.
          - use SQLAlchemy higher level tools (ORM) for query creation,
          - first use: fill database from input (log) stream


        Expect to use derived classes specializing over a specific DB schema or table,
        e.g. NestedTreeDbOperator in ext_db.py
    """
    def __init__(self, remote_fields, remote_name, remote_key, connect_string):

        SQLAlchemyORMBackBase.__init__(self, remote_fields, remote_name,
                                             remote_key, connect_string)

    def createDeferredClasses(self, outerClass):
        """
        This creates the classes which are handled via the  Deferred Base protocol/paradigm

        Arg: outerClass is a class which has a method 'mkClasses' that will make
             application oriented classes compliant with the Deferred Base protocol of ORM

        """
        rbase,base = self.getReflectedBase()
        self.db_gen_outer =  outerClass(rbase, base) 
        self.classDict =  self.db_gen_outer.mkClasses()
       
        for clNm,cl in self.classDict.items():
            self.registerReflected(clNm, cl)
            logging.debug(f"In {type(self)}.createDeferredClasses, registered {clNm}:{cl}")
            
             
    def operate(self, field, value, row):
        """ perform the operate query :
        """
        self._operate_init()
        return self._operate_fill(field, value, row)
    

    def _create_query_stmts(self):
        pass                

