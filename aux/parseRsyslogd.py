#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: Python -*-
#
# (C) Alain Lichnewsky, 2021
#

import os
import sys
import locale
import argparse
import traceback
import logging

from collections.abc import Iterable
from functools import reduce
from io import StringIO

import re

if __name__ == '__main__':
    path  = ["/home/alain/src/logtools"]
    path.extend(sys.path)
    sys.path  = path
    if "-d" in sys.argv:
        ps = '\n\t'.join(sys.path)
        print( f"sys.path:{ps}", file = sys.stderr)


import logtools
from logtools._config import setLoglevel
from logtools.parsers2 import count, RSyParsing, printAvailTemplates


if __name__ == '__main__':
    description =""" 
    This builds and tests syslog template based parser(s)

    Example:
            docker container logs mysql1  2>/dev/stdout >/dev/null | \
	    ~/src/logtools/aux/parseRsyslogd.py -v -d --testfile /dev/stdin
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
        
        argLineParser.add_argument("-i","--tmpltnum" , type = int,
                                  dest="tmpltnum",
                                  help="Designate template number in prefefined table")

        argLineParser.add_argument("-t","--tmpltname" , type = str,
                                  dest="tmpltname",
                                  help="Designate template by name in prefefined table")

        
        argLineParser.add_argument("-s","--sym" , type = str,
                                  dest="logLevSym",
                                  help="logging level (symbol)")

        argLineParser.add_argument("-n","--num" , type=int , 
                                  dest="logLevVal",
                                  help="logging level (value)")

        argLineParser.add_argument("--testfile" , type=str , 
                                  dest="testFileName",
                                  help="test filename/path, each line will be parsed")


        try:
            options = argLineParser.parse_args()
            if options.doDebug:
                sys.stderr.write (f"options:{repr(options)}\n")
            setLoglevel(options)

            
            c = count(lambda x: x is not None, (options.tmpltnum, options.tmpltname))
            if c == 0:
                options.tmpltnum = 1
                options.tmpltname = 'TraditionalFileFormat'
            elif c  == 1:
                if options.tmpltnum is not None:
                    options.tmpltname = RSyParsing.tmplIdx[ options.tmpltnum ] 
                elif options.tmpltname:
                    options.tmpltnum = RSyParsing.tmplDict[options.tmpltname][2]
                else:
                    raise ValueError( "Incorrect specification of flags --tmpltname and --tmpltnum" )
            else:
                print("Must specify  at most one of --tmpltnum --tmpltname",
                      file= sys.stderr)
                sys.exit(1)
                
            logging.info(  f"Testing pattern  {options.tmpltname} { options.tmpltnum}\n"
                          +f"\t{RSyParsing.tmplDict[options.tmpltname]}")
            
            rsymParser = RSyParsing( options.tmpltname,
                                     *RSyParsing.tmplDict[options.tmpltname][0:2])
            if options.testFileName:
                testParser( options.testFileName, rsymParser)
            
        except KeyError as err:
            print(f"ERROR specification of non existent template number or name\n\t{err}",
                  file = sys.stderr)

            printAvailTemplates(tmplDict, tmplIdx)
            sys.exit(2)
        except Exception:
            sys.stderr.write ( "Quitting because of error(s)\n" )
            traceback.print_exc()
            sys.exit(1)


    def testParser(infilename, rsymParser):
        with open(infilename,"r" ) as infile:
            for line in infile:
                logging.info(f"trying line:{repr(line)}")
                rsymParser.parse(line)

    mainPgm()

    
