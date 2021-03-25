#!/usr/bin/env python3
#
#  (C) Alain Lichnewsky, 2021
#

"""
    Facilitate running tests manually


    Environ requirements : 
          - TESTDATADIR must point to directory "aux/testData"
                        otherwise a RuntimeError is issued
          - ZTESTPGM    must point to file test_logtools.py
                        otherwise a RuntimeError is issued
          - ZTESTPGMPYPATH if defined TESTPGM is run with PYTHONPATH=$TESTPGMPYPATH
                        otherwise no modification of PYTHONPATH
"""

import sys, os
import argparse
import traceback
import logging

nbErrors = 0
errList  = []

# ---------------------------------------------------------------------- Setup Env        
testDataDir, ztestpypath, ztestpgm  = map( os.getenv,
                                          ("TESTDATADIR", "ZTESTPGMPYPATH", "ZTESTPGM"))
missing=[]
if testDataDir is None:
    missing.append("TESTDATADIR")
if ztestpgm is None:
    missing.append("ZTESTPGM")

if len(missing):    
    msg = "Missing environment variable(s)" + " and ".join(missing) 
    logging.error(msg)
    raise RuntimeError(msg)

if ztestpypath is None:
     ztestpypath  = ""
# ---------------------------------------------------------------------- Setup Env        



# Note: (development testing)
# This should run without "pip installing" "logtools", therefore we include this

def setLoglevel(options):
    """ Customize logging level, using options dictionnary collected from CLI
    """
    if options.logLevSym and options.logLevVal:
        print("Flags --sym and --num are exclusive", file = sys.stderr )
        sys.exit(1)
    try :
        basics  ={'format' : "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}
        if options.logLevVal:
            basics['level'] = options.logLevVal
        elif options.logLevSym:
            basics['level'] = options.logLevSym 
        logging.basicConfig(**basics)
        
    except ValueError as err:
        print( f"Bad --sym or --num flag value\n\t{err}", file = sys.stderr)
        sys.exit(2)
    except Exception as err:
        print( f"Unexpected error\n\t{err}", file = sys.stderr)
        raise

def  docTestDict():
     s = ""
     for k,v in testDict.items():
         s += (k + "\t:" + v + "\n")
     return s
 

def systemRun(shellCmd):
    global nbErrors
    print("About to run: " + shellCmd)
    
    retcd = os.system( shellCmd )
    if retcd:
         nbErrors += 1
         raise RuntimeError("Command has failed")
    else:
        print("Ran shellCmd")

    
def test(letter,options):
    shellCmd = testDict[letter]
    try: 
        systemRun(shellCmd)
    except Exception as err:
        logging.error( f"Test '{letter}' failed with '{err}'")
        errList.append(letter)
        if not options.doContinue:
            raise err




testDict={
    "A" : """cat %s/TestAuth.data | 
	      filterbots -s ERROR -r ".*uid (?P<ip>\d+).* obtain (?P<ua>[^\s]+)" --print 2>/dev/null
           """ % testDataDir,

    "B" : """gunzip --stdout %s/TestApport*.gz | 
	      filterbots -s ERROR -r ".*pid 9\d+\).*"  --print 2>/dev/null
          """ % testDataDir,

    "C" : """gunzip --stdout %s/TestAuth*.gz | 
              filterbots -s ERROR -r ".*" --print 2>/dev/null | aggregate -d' ' -f1-5
          """ % testDataDir,

    "D" : """gunzip --stdout  %s/TestAuth*.gz  | 
             cat  -   %s/TestAuth.data|  
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*" \
              --print
          """ % (testDataDir, testDataDir),
 
    "E" : """gunzip --stdout  %s/TestAuth*.gz | cat - %s/TestAuth.data |
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*"  --print
          """ % (testDataDir, testDataDir) ,

    "F" : """cat %s/TestAuth.data  | 
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*"  --print
          """  % testDataDir ,

    "G" : """cat %s/TestAuth.data | 
             logparse --parser TraditionalFileFormat -f 3 -s ERROR 
          """ % testDataDir,

    "H" : """cat %s/TestAuth.data    | 
             logparse --parser TraditionalFileFormat -f msg -s ERROR 
          """ % testDataDir,

    "I" : """cat %s/TestAuth.data  | 
             logparse --parser TraditionalFileFormat -f TIMESTAMP -s ERROR
          """ % testDataDir,

     "J" : """cat %s/testRFC5424.data | 
              logparse --parser SyslogRFC5424 -f hostname -s INFO
           """ % testDataDir,

     "K" :  """cat %s/testCommonLogFmt.data | 
               logparse --parser CommonLogFormat  -s INFO -f4
            """ % testDataDir,

     "L" :  """logmerge -d' ' -f1 %s/TestAuth.data %s/testRFC5424.data
            """ % (testDataDir,testDataDir ) ,

     "M" :  """logmerge --parser CommonLogFormat -f4 %s/testCommonLogFmt.data
            """ % testDataDir,

     "N" :  ( "cat %s/testCommonLogFmtXL.data | "  % testDataDir  +
             """ logparse --parser AccessLog \
                  --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"' \
                  -f1,2 -s DEBUG
             """),

     "O" :  ("cat %s/testCommonLogFmtXL.data | "  %  testDataDir +
             """logparse --parser AccessLog \
                   --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"'  \
                   -f8,9
             """),

     "P" :  """logmerge -d' ' -f3 \
                  --numeric %s/testRFC5424.data --parser SyslogRFC5424
             """ %  testDataDir,

     "Q" :  """logmerge -d' ' -f1 \
                   %s/TestAuth.data %s/testRFC5424.data
             """ %  ( testDataDir, testDataDir) ,
       
     "R" :  ("cat %s/testCommonLogFmt.data | " % testDataDir +
             """ qps -r'^(.*?) org' --dateformat '%b %d, %Y %I:%M:%S %p'  \
                        -W15 --ignore 
             """ ),
     
     "S" :  """logmerge -d' ' -f1 \
                   %s/testRFC5424.data %s/testRFC5424.data \
                   --parser SyslogRFC5424
             """ % (  testDataDir,  testDataDir),

     "Z" :   "%s  python3 %s" % ( ztestpypath,  ztestpgm )
    }
    
if __name__ == '__main__':
    description = """ 
    Run tests according to key:
"""
    
    def mainPgm():
        global description
        global nbErrors
        global errList
        
        description += docTestDict()
        
        argLineParser = argparse.ArgumentParser(
            description = description,
            formatter_class=argparse.RawDescriptionHelpFormatter  )

        argLineParser.add_argument( "keyLetter" )
        
        argLineParser.add_argument("-d","--debug" ,action="store_true",
                                  dest="doDebug",
                                  help="Debug messages on stderr")

        argLineParser.add_argument("-c","--continue" ,action="store_true",
                                  dest="doContinue",
                                  help="do not stop on error")

        argLineParser.add_argument("-s","--sym" , type = str,
                                  dest="logLevSym",
                                  help="logging level (symbol)")

        argLineParser.add_argument("-n","--num" , type=int , 
                                  dest="logLevVal",
                                  help="logging level (value)")


        
        
        try:
            options = argLineParser.parse_args()

            setLoglevel(options)

            if options.doDebug:
                sys.stderr.write (f"options:{repr(options)}\n")
                
            if options.keyLetter and options.keyLetter != "+":
                if options.keyLetter in testDict:
                    test(options.keyLetter, options)
                else:
                    print(f"Bad keyLetter positional argument:{options.keyLetter}",
                          file=sys.stderr)
                    sys.exit( 1 )
            else:
                for letter in testDict:
                    test(letter, options)

                         
        except Exception:
            sys.stderr.write ( "Quitting because of error(s)\n" )
            traceback.print_exc()

        if nbErrors:
           logging.info(f"Execution of tests produced {nbErrors} errors\n\tFailed:{repr(errList)}")
           sys.exit(1)
        else:
           logging.info("No errors produced")
            
    mainPgm()

    
