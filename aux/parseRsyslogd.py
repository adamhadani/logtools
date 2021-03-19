#!/usr/bin/python3

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

## For development environment REMOVE ONCE/IF INSTALLED *****************
## this is normally found in logtools/_config.py

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
## ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


def count(func,iter):
    """ Count number elements in iter where func returns true
    """
    def c(x):
        return 0 if not x  else 1
    return reduce(int.__add__, map( func, iter), 0)

#
# These are the templates considered; when extending keep in mind:
#     - "FileFormat" must be first.
#     - default "TraditionalFileFormat" must be second corresponding to "-n 1"
#
#  Make sure to escape backslash !
#
templateDefs = """ 
#$template FileFormat,"%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\\n"

#$template TraditionalFileFormat,"%TIMESTAMP% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\\n"

#$template ForwardFormat,"<%PRI%>%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag:1:32%%msg:::sp-if-no-1st-sp%%msg%"

#$template TraditionalForwardFormat,"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag:1:32%%msg:::sp-if-no-1st-sp%%msg%"

"""

templateNotConsidered = """
#$template StdSQLFormat,"insert into SystemEvents (Message, Facility, FromHost, Priority, DeviceReportedTime, ReceivedAt, InfoUnitID, SysLogTag) values ('%msg%', %syslogfacility%, '%HOSTNAME%', %syslogpriority%, '%timereported:::date-mysql%', '%timegenerated:::date-mysql%', %iut%, '%syslogtag%')",SQL

#$template jsonRfc5424Template,"{\\"type\\":\\"mytype1\\",\\"host\\":\\"%HOSTNAME%\\",\\"message\\":\\"<%PRI%>1 %TIMESTAMP:::date-rfc3339% %HOSTNAME% %APP-NAME% %PROCID% %MSGID% %STRUCTURED-DATA% %msg:::json%\\"}\\n"

"""


def prepareTemplateDict(tempStr):
    """ Build tables for selecting rsyslogd parsers by name of template. It is
        expected that all parsers corresponding to these names will be made 
        available based on parser name. This may imply augmenting the parser
        selection mechanism in parser.py.
    """
    # A template consists of a template directive, a name, the actual template
    # text and optional options.
    rexs= ( "^(\#?\$?template)\s+",                 # template directive
            "(?P<name>[A-Za-z0-9_@]+)\s*,\s*",      # name
            "\"(?P<template>[^\"]*)\""              # template
            "(\s*,\s*(?P<option>[A-Za-z]+))*\s*$"   # option part, case insensitive
          )
    rex = re.compile("".join(rexs), re.VERBOSE)
    rexblank = re.compile("^\s*\n?$")
    
    tmplDict = {}
    tmplIdx  = {}
    def splitLine(l):
        nl = l.replace("\\\"","\\@")
        mobj = rex.match(nl)
        
        if mobj:
            return mobj.groupdict()
        else:
            raise ValueError( f"NO MATCH for line {expr(l)}")
        return nl
    
    with StringIO(tempStr) as input:
        i = -1
        for line in input:
            if rexblank.match(line):
                continue
            i += 1
            flds = splitLine(line)
            name = flds['name']
            if name in tmplDict :
                raise RuntimeError(f"Multiply defined template name {name}")
            tmplDict[name] = (flds['template'], flds['option'], i)
            tmplIdx[i] = name
    return (tmplDict, tmplIdx)

def printAvailTemplates(tmplDict, tmplIdx, file = sys.stderr):
    tmplnames = tmplDict.keys()
    print(f"Available templates: {tmplnames}", file = file)
    print(f"Number associations: {tmplIdx}", file = file)


class RSyParsing():
    """ This class builds a rsyslog parser from its specs and then permits to 
        operate it.
    """
    def __init__(self, name, spec, options):
        logging.debug(f"In {type(self).__init__}: name:{name}\n\t{spec}\n\t{options}")

        self.name = name
        self.spec = spec
        self.options = options
        self.rexNamedGroups = {}
        self._compile()
 
       
    rexs = "^(?P<txt>[^%]+)?%(?P<replacer>[^%]+)%"
    rexends = "^(\s+|\\\\n)$"
    rexbads  = "^({|insert\s+into)"
    def _compile(self):
        rex = re.compile( RSyParsing.rexs)
        rexend = re.compile( RSyParsing.rexends)
        if re.match( RSyParsing.rexbads, self.spec):
            raise NotImplementedError(f"Spec has not supported (yet?) format:\n{self.spec}")

        spec = self.spec
        decompose = []
        while len(spec)>0:
            mobj = rex.match(spec)
            if mobj:
                decompose.append(mobj.groupdict())
                span= mobj.span()
                spec = spec[span[1]:]
            else:
                mobjEnd = rexend.match(spec)
                if mobjEnd :
                    break
                print(f"For spec:{self.spec}\n\tdecomposed:{decompose}", file = sys.stderr)
                raise RuntimeError(f"Could not match at end: '{spec}' (len:{len(spec)})")
        logging.debug(f"Decomposed {self.spec}\n\tinto{decompose}")

        buildList = []
        for el in decompose:
            if el['txt'] is not None:
                buildList.append(el['txt'])
            if el['replacer'] is not None:
                buildList.append(self._replacer(el['replacer']))

        build = "".join(buildList)
        try : 
            self.builtRex = re.compile(build)
            logging.debug(f"Compiled regexp {self.builtRex}")
        except re.error as err:
            logging.error(f"Unable to re.compile {build}\n\t{err}")


    #  The idea is to accomodate logs on my Linux/Ubuntu/FR installation.
    #  Following regexps are made NOT IN  ACCORDANCE with standards
    #     ( which are too complicated at least for now) :
    #                    https://tools.ietf.org/html/rfc5424
    # 			 https://tools.ietf.org/html/rfc5234 (BNF def)
    # 			 https://tools.ietf.org/html/rfc3339 (Timestamp)
    #  unless otherwise noted. If you need compliance see class SyslogRFC5424,
    #  making use of  https://github.com/EasyPost/syslog-rfc5424-parser. 
    #
    def A(x):
        "Provides abbreviations for recurring subpatterns"
        pass
    A.let             = "[A-Za-z]"
    A.lets            = "[A-Za-z]+"
    A.Lets            = "[A-Z][A-Za-z]*"
    A.digits          = "\d+"
    A.let_dig         = "([A-Za-z]|\d)"
    A.let_digS        = "([A-Za-z]|\d)+"
    A.let_dig_hyp_pt  = "(" + A.let_dig + "|[.-])"
    A.let_dig_hyp_ptS = "(" + A.let_dig + "|[.-])+"
    A.let_dig_hyp     = "(" + A.let_dig + "|[-])"
    A.let_dig_hypS    = "(" + A.let_dig + "|[-])+"
    A.tstampEmpirical = (A.Lets + "\s" +  A.digits + ":" + A.digits + ":" + A.digits )
    A.tstampEmpDpkg   = (  A.digits + "-" + A.digits + "-" + A.digits + "\s" +
                           A.digits + ":" + A.digits + ":" + A.digits )

    syslogFldRexDict = {
        'HOSTNAME' : "(" + A.let_dig + A.let_dig_hyp_pt + "*" + A.let_digS + \
                     "|" + "\d+(\.\d+)*"
                     ")",                             # not compliant RFC
        'TIMESTAMP': ( "(" + A.tstampEmpirical +      # not compliant RFC:seen syslog
                       "|" + A.tstampEmpDpkg +        # not compliant RFC:seen dpkg.log
                       ")"
                     ), 
        'syslogtag': "[^:]+:",
        'msg':".*",
        'PRI':"<[^>]{3,5}>"
        }

    
    def _replacer(self, replId):
        # Notes:1) that property options are documented at
        #         https://www.rsyslog.com/doc/v8-stable/configuration/property_replacer.html
        #       2) I am not even trying to be compliant...., still want to parse
        #         template descriptions
        splitRId = replId.split(":") 
        if len(splitRId) > 1:
            logging.debug(f"Ignored property options:{splitRId[1:]}")
            replId = splitRId[0]
        if replId in  RSyParsing.syslogFldRexDict:
           return  ( "(?P<" + self._uniqueNameGroups(replId) +">"
                     +  RSyParsing.syslogFldRexDict[replId]
                     +")" )
        else:
           raise ValueError(f"Regexp symbolic field name not found:{replId}")
       
    def _uniqueNameGroups(self, nm):
        if nm in self.rexNamedGroups:
            self.rexNamedGroups[nm] += 1
            return nm+str(self.rexNamedGroups[nm])
        else:
           self.rexNamedGroups[nm] = 0
           return nm

    def parse(self, text):
        mobj =  self.builtRex.match(text)
        if mobj :
            logging.info(f"Match for text\n\t{text}\n\t{mobj.groupdict()}\n\t{mobj.span()}")
        else:
            logging.error(f"No match for text\n\t{repr(text)}")
        
if __name__ == '__main__':
    description =""" 
    This builds and tests syslog template based parser(s)
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
                
            tmplDict, tmplIdx = prepareTemplateDict(templateDefs)
            
            c = count(lambda x: x is not None, (options.tmpltnum, options.tmpltname))
            if c == 0:
                options.tmpltnum = 1
                options.tmpltname = 'TraditionalFileFormat'
            elif c  == 1:
                if options.tmpltnum is not None:
                    options.tmpltname =  tmplIdx[ options.tmpltnum ] 
                elif options.tmpltname:
                    options.tmpltnum =   tmplDict[options.tmpltname][2]
                else:
                    raise ValueError( "Incorrect specification of flags --tmpltname and --tmpltnum" )
            else:
                print("Must specify  at most one of --tmpltnum --tmpltname",
                      file= sys.stderr)
                sys.exit(1)
                
            logging.info(  f"Testing pattern  {options.tmpltname} { options.tmpltnum}\n"
                          +f"\t{tmplDict[options.tmpltname]}")
            
            rsymParser = RSyParsing( options.tmpltname, *tmplDict[options.tmpltname][0:2])
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

    
