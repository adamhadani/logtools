#!/usr/bin/env python3
#
#  (C) Alain Lichnewsky, 2021
#

"""
    Facilitate running tests manually
"""

import sys, os
import argparse
import traceback
import logging

nbErrors = 0
errList  = []

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
    "A" : """cat /var/log/auth.log | 
	      filterbots -s ERROR -r ".*uid (?P<ip>\d+).* obtain (?P<ua>[^\s]+)" --print 2>/dev/null
           """,

    "B" : """gunzip --stdout /var/log/apport.log.*.gz | 
	      filterbots -s ERROR -r ".*pid 9\d+\).*"  --print 2>/dev/null
          """,

    "C" : """gunzip --stdout /var/log/auth.log.*.gz | 
              filterbots -s ERROR -r ".*" --print 2>/dev/null | aggregate -d' ' -f1-5
          """,

    "D" : """gunzip --stdout /var/log/auth.log.*.gz | 
             cat /var/log/auth.log -  |  
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*" \
              --print
          """,
 
    "E" : """gunzip --stdout /var/log/auth.log.*.gz | cat /var/log/auth.log -  |
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*"  --print
          """,

    "F" : """cat testData/TestAuth.data  | 
             filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*"  --print
          """,

    "G" : """cat testData/TestAuth.data | 
             logparse --parser TraditionalFileFormat -f 3 -s ERROR 
          """,

    "H" : """cat testData/TestAuth.data    | 
             logparse --parser TraditionalFileFormat -f msg -s ERROR 
          """,

    "I" : """cat testData/TestAuth.data  | 
             logparse --parser TraditionalFileFormat -f TIMESTAMP -s ERROR
          """,

     "J" : """cat testData/testRFC5424.data | 
              logparse --parser SyslogRFC5424 -f hostname -s INFO
           """,

     "K" :  """cat testData/testCommonLogFmt.data | 
               logparse --parser CommonLogFormat  -s INFO -f4
            """,

     "L" :  """logmerge -d' ' -f1 testData/TestAuth.data testData/testRFC5424.data
            """,

     "M" :  """logmerge --parser CommonLogFormat -f4 testData/testCommonLogFmt.data
            """,

     "N" :  """cat testData/testCommonLogFmtXL.data | 
               logparse --parser AccessLog \
                  --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"' \
                  -f1,2 -s DEBUG
             """,

     "O" :  """cat testData/testCommonLogFmtXL.data | 
                logparse --parser AccessLog \
                   --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"'  \
                   -f8,9
             """,

     "P" :  """logmerge -d' ' -f3 \
                  --numeric testData/testRFC5424.data --parser SyslogRFC5424
             """,

     "Q" :  """logmerge -d' ' -f1 \
                   testData/TestAuth.data testData/testRFC5424.data
             """,
       
     "R" :  """cat testData/testCommonLogFmt.data | 
                qps -r'^(.*?) org' --dateformat '%b %d, %Y %I:%M:%S %p'  \
                        -W15 --ignore 
             """,
     
     "S" :  """logmerge -d' ' -f1 \
                   testData/testRFC5424.data testData/testRFC5424.data \
                   --parser SyslogRFC5424
             """,

     "Z" :   """PYTHONPATH="$HOME/src/logtools"
               python3 ~/src/logtools/logtools/test/test_logtools.py
             """
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
        else:
           logging.info("No errors produced")
            
    mainPgm()

    
