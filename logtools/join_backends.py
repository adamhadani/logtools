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

from .ext_db import DB_Tree_Maker,  dictOfDictIterator, TREEPOS


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
        engine = self.db
        try:
            query_stmt = ( self.query_stmt_dict["wherekey"]
                            if len(key)>0 else self.query_stmt_dict[None] )

            logging.debug(f"{type(self)}.join toexecute db query with key={key}" +
                          f"and query={query_stmt}")

            result = self.connection.execute( text(query_stmt), key=key)
            for row in result:
                yield row
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
        self.reflectedList = []  # for using  DeferredReflection 
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

    def registerReflected(self,cl):
        """ register class that will need preparation, to be effected by method
            prepareDeferred
        """
        self.reflectedList.append(cl)

    def prepareDeferred(self):
        for cl in self.reflectedList:
            logging.debug(f"about to prepare for class:{cl}")
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
        """ perform the join query :
            TBD: see if we wouldn't prefer a general query execution method
            (not limited to join)
        """
        try:
            query = ( self.query_stmt_dict["wherekey"]
                      if len(key)>0 else self.query_stmt_dict[None] )
            q = query(metadata=self.metadata, selvalue=key)
            result = self.session.execute(q)
            logging.debug(f"In {type(self)}.join result returned from execute:{type(result)}{result}")

            for row in result:
                yield row
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

    """
    def __init__(self, remote_fields, remote_name, remote_key, connect_string):

        SQLAlchemyORMBackBase.__init__(self, remote_fields, remote_name,
                                             remote_key, connect_string)

    def createDeferredClasses(self):
        """
        This creates the classes which are handled via the  Deferred Base protocol/paradigm

        """
        rbase,base = self.getReflectedBase()
        self.db_tree_maker =  DB_Tree_Maker(rbase, base) 
        self.classDict =  self.db_tree_maker.mkClasses()
       
        for clNm,cl in self.classDict.items():
            self.registerReflected(cl)
            logging.debug(f"In {type(self)}.createDeferredClasses, registered {clNm}:{cl}")

             
    def operate(self, field, value, row):
        """ perform the operate query :
        """
        self._operate_init()

        return self._operate_fill(field, value, row)
    
    def _operate_init(self):
        # fetch uniqueId from tree with parent_id == 0 
        self.uniqueId = self._fetch_unique_id()
        self.dateIdent = datetime.today().isoformat(timespec='microseconds')
        self.parentStack = []

    def _store_unique_id(self):
        TreeNode =  self.classDict["TreeNode"]
        node = (self.session.query(TreeNode).filter_by(id=0))[0]
        print(f"In store unique type(node)={type(node)}{node}", file=sys.stderr)
        nid = str( (self.uniqueId + 99) // 100  * 100)
        node.nval= nid
        logging.debug(f"New First Avail unique id:{nid}")
        self.session.commit()
    
    def _fetch_unique_id(self):
        """ Fetch the first avaiable UniqueId, create the special entry if it 
            does not exist.
        """
        # At locations 0..99, we store special stuff
        #  0 : nval = next available unique id, parent = None, name="FirstAvailUID", 
        #
        TreeNode =  self.classDict["TreeNode"]
        uid = None
        for nval in self.session.query(TreeNode.nval).filter_by(id=0):
            uid = int(nval[0])
        if uid is None:
            node = TreeNode(0, "FirstAvailUID", nval=1000)
            self.session.add(node)
            self.session.commit()
            uid = 1000
        return uid
    
    def _operate_fill(self, field, value, row):
        """ Fill from a dict of dict
        """

        # RootNode is special, identify each input by date time, permit
        #          to version, delete old stuff etc...
        #          it is likely that the range of uniqueIds will be stuffed somewhere
        #          to avoid an awkward query
        #          Reserve RootNode.Id + 1,...., RootNode.Id+9 for special nodes
        #              RootNode.Id + 1 : begin unique Id range for a session
        #                          + 2 : end  unique Id  range (but in range!)

        firstAvailUniqueId =  self.uniqueId + 10
        root_parent_id = self.uniqueId
        self.enterNode(self.dateIdent, ["RootNode"])
        self.enterNode( firstAvailUniqueId, ["RangeStart"], parent_id = root_parent_id,
                        fillOnly = True)
        self.uniqueId = firstAvailUniqueId
        
        for (val, path) in dictOfDictIterator(value):
            logging.debug(f"Walking: path={path}, val={val}")
            if val in (TREEPOS.LIST,TREEPOS.TOP):
               self.enterNode(val, path)
            elif val == TREEPOS.POP:
               self.popNode(val, path)
            else:
               self.enterNode(val, path, fillOnly=True)

        rootnode = self.parentStack[0]
        self.session.add(rootnode)

        self.enterNode( self.uniqueId-1, ["RangeEnd"], parent_id = root_parent_id,
                        fillOnly = True)
        
        logging.debug(f"Committing!!")      
        self.session.commit()
        self._store_unique_id()
        
        return ()
        
    def enterNode(self, val, pos, fillOnly=False, parent_id=None):
        """
            Enter a node in the DB table, if fillOnly is False, the
            node is also entered on the parentStack, and will need to be 
            popped.
              - fillOnly == True: filling a tree node or a list node
              - fillOnly == False: entering a new nested level of list or tree node
        """
        TreeNode =  self.classDict["TreeNode"]
        args={}
        if parent_id is None:
            args['parent'] = self.parentStack[-1].id  if len(self.parentStack) > 0 else None
        else:
            args['parent'] = parent_id
        args['nval'] = val 
        sid = pos if isinstance(pos, str) else ( pos[-1] if len(pos)>0 else "**TOP**" )
        
        node = TreeNode(self.uniqueId, sid, **args)
        self.session.add(node)
        
        if not fillOnly:
            self.parentStack.append(node)
        self.uniqueId+=1

        logging.debug(f"In {type(self)}.enterNode: pos={pos} uniqueId={self.uniqueId-1}"
                      +f"\n\tstack len={len(self.parentStack)}"
                      +f"\n\targs={args}" )


        
    def popNode(self, val, pos):
        self.parentStack.pop()

    def _create_query_stmts(self):
        pass                

