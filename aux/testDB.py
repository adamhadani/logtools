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
aux/testDB.py: test tool of module logtools.ext_db, separated to avoid 
requiring ``hypothesis'' in logtools.

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

from logtools.ext_db import DB_Tree_Maker, TREEPOS, dictOfDictIterator

# ................................................................................
# Random Test Generation stuff (based on hypothesis package)
# ................................................................................

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

# ................................................................................


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
            print(f"\tr={r[1]}\t->\t{r[0]}")   



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

NOTE: In this version, testing is done by visual inspection, need to develop
      automatic verification
"""
    print(description)
    sys.exit(0)

if "-v" in sys.argv:
    sys.argv = [x for x in sys.argv if x != "-v"]
    TestEncoding.DO_DEBUG_PRINT = True
    sys.stderr.write("Set verbose mode\n")

unittest.main()
