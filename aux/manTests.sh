#!/bin/bash

# ------------------------------------------------------------------------------
#    This is script to estabish environment for running the test program
# ------------------------------------------------------------------------------
#    Environ requirements for entering TESTPGM: 
#          - TESTDATADIR must point to directory "aux/testData"
#            otherwise a RuntimeError is issued
#          - ZTESTPGM       must point to file test_logtools.py
#          - ZTESTPGMPYPATH if defined TESTPGM is run with PYTHONPATH=$TESTPGMPYPATH
#                           otherwise no modification of PYTHONPATH
#
#           Here, if BASEDIR is defined, it will be used as the base for all paths,
#                 otherwise $HOME is used
# ------------------------------------------------------------------------------

BASEDIR=${BASEDIR:=${HOME}}
export PYTHONPATH="$BASEDIR/src/logtools/"
export ZTESTPGM="$BASEDIR/src/logtools/logtools/test/test_logtools.py"
export TESTDATADIR="$BASEDIR/src/logtools/aux/testData"
TESTPGM="$BASEDIR/src/logtools/aux/manTests.py"

echo args=$*
python3 $TESTPGM $*


