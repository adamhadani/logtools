#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: Python -*-
#
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
logtools.ext_db.py

Data Base specifications and definition as SQLAlchemy "Mapped Classes", this is
used in particular by _db.py and the tool logdb(.py)
"""

import os
import re
import sys
import logging

from functools import partial
from copy import copy
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from enum import Enum

from datetime import datetime
import json

from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import Session, registry
from sqlalchemy.orm import declarative_base

from sqlalchemy import ForeignKey
from sqlalchemy.orm import backref
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from sqlalchemy.sql import text

# Apparently here we may encounter a SQLAlchemy version in transition to the ORM i/f ++
try:
    from sqlalchemy.orm import select
except Exception:
    from sqlalchemy.sql import select
# END ORM transition ............................................................... ++

from .join_backends import SQLAlchemyDbOperator


class DB_Tree_Maker():
    """
    This class builds a (set of) mapped classe(s) to represent dict of (list dict)
    with the intent to represent JSON entries.

    Technically, the built mapped classes are intended for using Deferred Reflection
    as supported by logtools.join_backends.SQLAlchemyORMBackBase.
    see https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html
    """

    def __init__(self, base, deferredBase):
        self.Base = base
        self.deferredBase = deferredBase

    def mkClasses(self):
        """ This will return the made up classes, which are compliant to the deferredBase
            method.
        """
        Base = self.Base
        DeferredBase = self.deferredBase

        class TreeNode(DeferredBase, Base):
            """ this representation of dict of dict as ``adjacency list'' is derived
                from an example in SQLAlchemy/examples/orm/examples.html.
                With modifications for deferred reflection from
                https://docs.sqlalchemy.org/en/14/orm/declarative_tables.html


                When 'parent_id' < 1000, entries permit to store some
                global data, indexed by name, with value (converted to string) in nval

                Reserved value : parent_id   val
                                 0           next value usable for self.uniqueId 
					        (autoincrement to be tested later)

            """

            __tablename__ = "tree" # do not enter the database name, it is auto.provided!
            __table_args__ = {'extend_existing': True} 
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey(id))
            name = Column(String(255), nullable=True)   # corresponds to SQL's VARCHAR
                                                        # SHA256 are 64 char long!!
            nval =  Column(String(255), nullable=True)

            children = relationship(
                "TreeNode",
                # cascade deletions
                cascade="all, delete-orphan",
                # many to one + adjacency list - remote_side
                # is required to reference the 'remote'
                # column in the join condition.
                backref=backref("parent", remote_side=id),
                # children will be represented as a dictionary
                # on the "name" attribute.
                collection_class=attribute_mapped_collection("name"),
            )

            def __init__(self, id, name, parent=None, nval=None):
                self.id   = id
                self.name = name
                self.parent_id = parent
                self.nval = nval

            def __repr__(self):
                return "TreeNode(name=%r, id=%r, parent_id=%r, nval=%r)" % (
                    self.name,
                    self.id,
                    self.parent_id,
                    self.nval
                )

            def dump(self, _indent=0):
                return (
                    "   " * _indent
                    + repr(self)
                    + "\n"
                    + "".join([c.dump(_indent + 1) for c in self.children.values()])
                )


            
        return {"TreeNode": TreeNode}
    

class NestedTreeDbOperator( SQLAlchemyDbOperator ):
    """ Specialization to enter JSON as nested (recursive) trees in a DB table

    """

    def __init__(self, remote_fields, remote_name, remote_key, connect_string):

        SQLAlchemyDbOperator.__init__(self, remote_fields, remote_name,
                                            remote_key, connect_string)

    
    def _operate_init(self):
        # fetch uniqueId from tree with parent_id == 0 
        self.uniqueId = self._fetch_unique_id()
        self.dateIdent = datetime.today().isoformat(timespec='microseconds')
        self.parentStack = []

    def _store_unique_id(self):
        TreeNode =  self.classDict["TreeNode"]
        node = (self.session.query(TreeNode).filter_by(id=0))[0]
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


    
class TREEPOS(Enum):
    """ Used in dictOfDictIteratorclass to characterize place in walked tree
    """
    EMPTY_TREE = 0
    TOP = 1
    LIST= 2
    POP = 3

    
def dictOfDictIterator(dodTree, pos=None):
    """ Walk iterator built with yield, to analyze a Dict of (list of) Dict structure,
        for instance obtained from JSON
    """
        
    if pos is None:
        pos =[]
    else:
        pos = copy(pos)
        
    if isinstance(dodTree, dict):
        if len(dodTree) == 0:
            yield(TREEPOS.EMPTY_TREE,pos)
        else:    
            first = True
            for k in dodTree:
                pos.append(k)
                for x in  dictOfDictIterator(dodTree[k],pos):
                    if first:
                        yield ( TREEPOS.TOP , pos[:-1])
                        first = False
                    yield x
                pos.pop()
            yield ( TREEPOS.POP, len(pos))
                
    elif isinstance(dodTree, Iterable) and not isinstance(dodTree,str):
        i = 0
        for k in dodTree:
            if i == 0:
                yield ( TREEPOS.LIST , pos)
            pos.append(i)
            for x in dictOfDictIterator(k,pos):
                yield x
            pos.pop()
            i+=1
        if i == 0:
            yield([],pos)
        else:
            yield ( TREEPOS.POP, len(pos))

    else:
        yield (dodTree,pos)

