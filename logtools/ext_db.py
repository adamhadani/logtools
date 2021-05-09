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

class TREEPOS(Enum):
    """ Used in dictOfDictIteratorclass to characterize place in walked tree
    """
    EMPTY_TREE = 0
    TOP = 1
    LIST= 2
    POP = 3

    
def dictOfDictIterator(dodTree, pos=None):
    """ Walk iterator built with yield
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

# ................................................................................
# Test stuff
# ................................................................................
if __name__ == "__main__":
    import unittest
    from hypothesis import given, assume, settings, HealthCheck
    import hypothesis.strategies as st


    MAX_SAMPLES = None
    if "-v" in sys.argv:
        MAX_SAMPLES = 5
        MAX_LEAVES = 8

    settings.register_profile("default", suppress_health_check=(HealthCheck.too_slow,))
    settings.load_profile(os.getenv(u'HYPOTHESIS_PROFILE', 'default'))
    if MAX_SAMPLES is None:
        MAX_LEAVES = 20
        MAX_SAMPLES = 50
    
    ALPHABET = ('A', 'B', 'C', ' ')
    ALPHABETK = ('a', 'b', 'c', '-')

    random_key_int = st.integers(0, 100)
    random_key_str = st.text(alphabet=ALPHABETK, min_size=2)
    random_key = random_key_str | random_key_int
    random_segments = st.lists(random_key, max_size=4)
    random_leaf = random_key_int | st.text(alphabet=ALPHABET, min_size=2)

    random_thing = st.recursive(
        random_leaf,
        lambda children: (st.lists(children, max_size=3)
                          | st.dictionaries( random_key_str
                                             | st.text(min_size=1, alphabet=ALPHABET),
                                             children)),
        max_leaves=MAX_LEAVES)

    random_node = random_thing.filter(lambda thing: (isinstance(thing, dict)
                                                     and len(thing)>1) )


    #
    # Run under unittest
    #
    class TestEncoding(unittest.TestCase):
        DO_DEBUG_PRINT = False

        @settings(max_examples=MAX_SAMPLES)
        @given(random_node)
        def test_walker(self, node):
            '''
            Test the yielding walker
            '''
            print(f"Entered test_walker, node={node}", file=sys.stderr)
            for r in dictOfDictIterator(node):
#                for z in r:
#                    print(f"\tz={z}")   
                print(f"\tr={r[1]}\t->\t{r[0]}")   

    
if __name__ == "__main__":
    if "-h" in sys.argv:
        description = """\
This may run either under tox or standalone. When standalone
flags -h and -v are recognized, other flags are dealt with by unittest.main
and may select test cases.

Flags:
    -h print this help and quit
    -v print information messages on stderr; also reduces MAX_SAMPLES to 50

Autonomous CLI syntax:
    python3 ext_db.py [-h] [-v] [TestWalker[.<testname>]]

    e.g.     python3 TestEncoding.test_match_re
"""
        print(description)
        sys.exit(0)

    if "-v" in sys.argv:
        sys.argv = [x for x in sys.argv if x != "-v"]
        TestEncoding.DO_DEBUG_PRINT = True
        sys.stderr.write("Set verbose mode\n")

    unittest.main()
