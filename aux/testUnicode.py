#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-
#
# (C) Alain Lichnewsky, 2021
#

import os
import sys
import re
import unicodedata



import unittest
from hypothesis import given, assume, settings, HealthCheck
import hypothesis.strategies as st

# using a try block so that this makes sense if exported to logtools/aux
# and used as a test case in this settings
try:
    import logtools.utils
except Exception as err:
    # This is related to the development environment -------------------
    from pathlib import Path
    home = str(Path.home())
    path  = [home + "/src/logtools"]
    if 'VENVPY' in os.environ:
        path.extend(os.environ['VENVPY'].split(":"))    
    path.extend(sys.path)
    sys.path  = path
    # END     related to the development environment -------------------
    
    import logtools.utils


# enables to modify some globals
MAX_SAMPLES = None
if __name__ == "__main__":
    if "-v" in sys.argv:
        MAX_SAMPLES = 50


settings.register_profile("default", suppress_health_check=(HealthCheck.too_slow,))
settings.load_profile(os.getenv(u'HYPOTHESIS_PROFILE', 'default'))
if MAX_SAMPLES is None:
    MAX_SAMPLES = 5

#Unicode alphabet
ALPHABET_UCWild = st.characters(
                    blacklist_characters="/?#", blacklist_categories=("Cs",))
ALPHABET_UCTame = st.characters(
                    blacklist_characters="/?#", blacklist_categories=("Cs",),
                    max_codepoint=0xFD, min_codepoint=0x40)

# somewhat restricted Greek
ALPHABET_UCGreek = st.characters(
                    blacklist_characters="/?#", blacklist_categories=("Cs",),
                    max_codepoint=0x3BF, min_codepoint=0x390)

# somewhat restricted Hebrew
ALPHABET_UCHebrew = st.characters(
                    blacklist_characters="/?#", blacklist_categories=("Cs",),
                    max_codepoint=0x5DF, min_codepoint=0x5BF)


# Combine a set of printables
ALPHABET_UC = st.one_of(ALPHABET_UCHebrew,   ALPHABET_UCGreek ,  ALPHABET_UCTame) 

# Recall
#Unicode Greek and Coptic: U+0370–U+03FF
#Unicode Hebrew block extends from U+0590 to U+05FF and from U+FB1D to U+FB4F.

random_uc_string = st.text(alphabet=ALPHABET_UC, min_size=2, max_size=8)


#
# Run under unittest
#
class TestEncoding(unittest.TestCase):
    DO_DEBUG_PRINT = False

    @settings(max_examples=MAX_SAMPLES)
    @given(random_uc_string)
    def test_ustring(self, s):
        '''  
          Show generated strings
        '''
        form = 'NFKD'
        sNorm = unicodedata.normalize(form, s)
        print(f"test_ustring received:'{s}',\tnormalized ({form}):'{sNorm}'",
              file=sys.stderr)


    @settings(max_examples=MAX_SAMPLES)
    @given(random_uc_string)
    def test_nustring(self, s):
        '''  
          Show generated strings
        '''
        form = 'NFKD'
        sNormEnc = unicodedata.normalize(form, s).encode('ascii','ignore')
        print(f"test_nustring received:'{s}',\tnormalized({form})/encoded(ascii) :'{sNormEnc}'",
              file=sys.stderr)


    @settings(max_examples=MAX_SAMPLES)
    @given(random_uc_string)
    def test_ucodeNorm(self, s):
        '''  
          Show generated strings
        '''
        form = 'NFKD'
        sNormEnc = logtools.utils.ucodeNorm(s)
        print(f"test_nustring received:'{s}',\tucodeNorm returns :'{sNormEnc}'",
              file=sys.stderr)
        

if __name__ == "__main__":
    if "-h" in sys.argv:
        description = """\
Function:
This is a test allowing to figure out in more detail the functionality
of the unicode python package.

This may run either under tox or standalone. When standalone
flags -h and -v are recognized, other flags are dealt with by unittest.main
and may select test cases.

Flags:
    -h print this help and quit
    -v print information messages on stderr; also reduces MAX_SAMPLES to 50

Autonomous CLI syntax:
    python3 [-h] [-v] [TestUnicode[.<testname>]]

    e.g.     python3 TestEncoding.test_match_re
"""
        print(description)
        sys.exit(0)

    if "-v" in sys.argv:
        sys.argv = [x for x in sys.argv if x != "-v"]
        TestEncoding.DO_DEBUG_PRINT = True
        sys.stderr.write("Set verbose mode\n")

    unittest.main()
