#!/usr/bin/env python

import os
import sys
import argparse
import traceback
import logging

from collections.abc import Iterable


def wrapit():
    first=True
    doWrap = False
    for l in sys.stdin:
        if first and l[0]=='[':
            doWrap = True
            sys.stdout.write('{"TOP":')
        sys.stdout.write(l[:-1])
    if doWrap:
        sys.stdout.write("}")
            

if __name__ == '__main__':
    description =""" 
    Wrap a list of dict representation to ensure top level is a dict,
    if it was a list it gets wrapped in the "TOP" entry of a dict.

    This is used to facilitate/permit parsing by a JSON parser.
    """

    def mainPgm():
        argLineParser = argparse.ArgumentParser(
           description = description,
           formatter_class=argparse.RawDescriptionHelpFormatter  )
        
        argLineParser.add_argument("-v","--verbose" ,action="store_true",
                                  dest="doVerbose",
                                  help="Verbose printout of debug oriented messages on stderr")
        argLineParser.add_argument("-d","--debug" ,action="store_true",
                                  dest="doDebug",
                                  help="Debug messages on stderr")

        try:
            options = argLineParser.parse_args()
            if options.doDebug:
                sys.stderr.write (f"options:{repr(options)}\n")
                
            wrapit()
            
        except Exception:
            sys.stderr.write ( "Quitting because of error(s)\n" )
            traceback.print_exc()
            sys.exit(1)
           

    mainPgm()

    
