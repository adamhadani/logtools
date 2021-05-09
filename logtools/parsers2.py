#!/usr/bin/env python
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

# ........................................ COPYRIGHT
#
# (C) Alain Lichnewsky, 2021
#     https://github.com/AlainLich
# ........................................ ******
#
"""
logtools.parsers2
Additional parsers for some common log formats,
These parsers can be used in a similar fashion as other logtools parsers
programmaticaly and via CLI. Additional parameters may be required (still to be
checked).
"""

import os
import re
import sys
import logging
from functools import partial
from datetime import datetime
from abc import ABCMeta, abstractmethod
from functools import reduce
from io import StringIO
from copy import copy

from syslog_rfc5424_parser import SyslogMessage, ParseError
import json
import dpath
import dpath.util

import logtools._config as _config
from ._config import AttrDict
from .parsers import LogParser, LogLine


#
# Little utility function ( could move to utils.py)
#

def count(func,iter):
    """ Count number elements in iter where func returns true
    """
    def c(x):
        return 0 if not x  else 1
    return reduce(int.__add__, map( func, iter), 0)


#
# Addition to handle Syslog RFC-5424
#

class SyslogRFC5424(LogParser):
    """ Parser for Syslog RFC-5424
    """
    def __init__(self):
        LogParser.__init__(self)
        self._logline_wrapper = LogLine()

    def parse(self, logline):
        "Parse log line "
        data = self._logline_wrapper

        logging.debug( f"Parsing RFC5424 line:{repr(logline)}")
        try:
            parsed = SyslogMessage.parse(logline)
            pdict = parsed.as_dict()

            data.fieldnames = pdict.keys()
            data.clear()
            for k, v in pdict.items():
                data[k] = v

            logging.debug( f"\tParsed(type(parsed)):{pdict}")
            return data
        except ParseError as err:
            logging.error( f"\tRFC5424 parse error:{err}")

        data.fieldnames = []
        data.clear()
        return data



#
# Addition to handle rsyslog RSYSLOG_TraditionalFileFormat (in a non compliant fashion)
#
# Documentation on "traditional templates" at url :
#      rsyslog-5-8-6-doc.neocities.org/rsyslog_conf_templates.html
#
# More standard rsyslog doc at
#      https://rsyslog-doc.readthedocs.io/en/latest/index.html
#      https://rsyslog-doc.readthedocs.io/en/latest/configuration/parser.html
#
# Much documentation at https://github.com/rsyslog


templateDefs = """
#
# These are the templates considered; when extending keep in mind:
#     - "FileFormat" must be first.
#     - default "TraditionalFileFormat" must be second corresponding to "-n 1"
#
#  Make sure to escape backslash !
#
#  Here : white lines, lines starting with "# " and lines with only 1 char "#" are ignored,
#         considered comment.
#
# ----------------------------------------------------------------------
#  Definitions from url : syslog-5-8-6-doc.neocities.org/rsyslog_conf_templates.html
#
#$template FileFormat,"%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\\n"

#$template TraditionalFileFormat,"%TIMESTAMP% %HOSTNAME% %syslogtag%%msg:::sp-if-no-1st-sp%%msg:::drop-last-lf%\\n"

#$template ForwardFormat,"<%PRI%>%TIMESTAMP:::date-rfc3339% %HOSTNAME% %syslogtag:1:32%%msg:::sp-if-no-1st-sp%%msg%"

#$template TraditionalForwardFormat,"<%PRI%>%TIMESTAMP% %HOSTNAME% %syslogtag:1:32%%msg:::sp-if-no-1st-sp%%msg%"

# ----------------------------------------------------------------------
# Docker log as output by command:  docker container logs <container-name>
# ----------------------------------------------------------------------
#$template DockerCLog,"%TIMESTAMP% %NUM% %bracket% %bracket% %bracket% %msg%"

# ----------------------------------------------------------------------

# To add  user specific templates, open a section RSysTradiVariant
# and insert an entry 'file' designating a file where templates are entered
# with the above format. The built function(s) will be added to module 'parser2'

# ----------------------------------------------------------------------


"""
#
# These are proposed templates for which I do not add here, however, concerning the
# second, see the JSON support in "class JSONParser" (parser.py)
#
templateNotConsidered = """
#$template StdSQLFormat,"insert into SystemEvents (Message, Facility, FromHost, Priority, DeviceReportedTime, ReceivedAt, InfoUnitID, SysLogTag) values ('%msg%', %syslogfacility%, '%HOSTNAME%', %syslogpriority%, '%timereported:::date-mysql%', '%timegenerated:::date-mysql%', %iut%, '%syslogtag%')",SQL

#$template jsonRfc5424Template,"{\\"type\\":\\"mytype1\\",\\"host\\":\\"%HOSTNAME%\\",\\"message\\":\\"<%PRI%>1 %TIMESTAMP:::date-rfc3339% %HOSTNAME% %APP-NAME% %PROCID% %MSGID% %STRUCTURED-DATA% %msg:::json%\\"}\\n"

"""

# A template consists of a template directive, a name, the actual template
# text and optional options.
_rexs= ( "^(\#?\$?template)\s+",                 # template directive
        "(?P<name>[A-Za-z0-9_@]+)\s*,\s*",      # name
        "\"(?P<template>[^\"]*)\""              # template
        "(\s*,\s*(?P<option>[A-Za-z]+))*\s*$"   # option part, case insensitive
      )
_rex = re.compile("".join(_rexs), re.VERBOSE)
_rexblank = re.compile("^(\s*|#( .*)?)\n?$")



def prepareTemplateDict(tempStr):
    """ Read the above set of templates and make dictionnaries permitting
        to access by name and also number. Numbers are convenient for
        typing reasons; expect you utility to display the nnumber -> name mapping
        using function 'printAvailTemplates' below

        This may require augmenting the parser selection mechanism in parser.py.
    """

    tmplDict = {}
    tmplIdx  = {}

    with StringIO(tempStr) as input:
         return addToTemplateDict(input, {}, {})


def addToTemplateDict(lines, tmplDict, tmplIdx, addFunction=False):
    """ Append templates to the dictionnaries, makes prepareTemplateDict modular
        so that we may add templates from configuration files
    """
    def splitLine(l):
        nl = l.replace("\\\"","\\@")
        mobj = _rex.match(nl)

        if mobj:
            return mobj.groupdict()
        else:
            raise ValueError( f"NO MATCH for line {repr(l)}")
        return nl

    i = len(tmplIdx)-1
    for line in lines:
        if _rexblank.match(line):
            continue
        i += 1
        flds = splitLine(line)
        name = flds['name']
        if name in tmplDict :
            raise RuntimeError(f"Multiply defined template name {name}")
        tmplDict[name] = (flds['template'], flds['option'], i)
        tmplIdx[i] = name
        
        if addFunction:
            thisModule = sys.modules[__name__]
            def fun( nm=None):
                return  RSysTradiVariant(nm)
            # The binding of arg (nm) and of fun is tricky
            setattr( thisModule , name  , partial(copy(fun), nm=name))

    return (tmplDict, tmplIdx)

    

def printAvailTemplates(tmplDict, tmplIdx, file = sys.stderr):
    tmplnames = tmplDict.keys()
    print(f"Available templates: {tmplnames}", file = file)
    print(f"Number associations: {tmplIdx}", file = file)


def addConfigFileSection():
    config = _config.logtools_config
    if "RSysTradiVariant" in config.sections():
        if "file" in config["RSysTradiVariant"]:
            with open(config["RSysTradiVariant"]["file"], "r") as fileTemplates:
                 (RSyParsing.tmplDict, RSyParsing.tmplIdx) = \
                     addToTemplateDict(fileTemplates,
                                       RSyParsing.tmplDict, RSyParsing.tmplIdx,
                                       addFunction = True) 


    
class RSyParsing():
    """ This class builds a rsyslog parser from its specs and then permits to
        operate it.
    """
    # class level static tables
    tmplDict, tmplIdx =  prepareTemplateDict(templateDefs)

    def __init__(self, name, spec, options):
        logging.debug(f"In {type(self)}{self}.__init__: name:{name}\n\t{spec}\n\t{options}")

        self.name = name
        self.spec = spec
        self.options = options
        self.rexNamedGroups = {}        
        self._compile()
        self._logline_wrapper = LogLine()
        

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


    #  The idea is to accommodate logs on my Linux/Ubuntu/FR installation.
    #  Following regexps (see package "re") are made NOT IN  ACCORDANCE with standards
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
    A.decnum          = "\d+(.\d+)?"
    A.let_dig         = "([A-Za-z]|\d)"
    A.let_digS        = "([A-Za-z]|\d)+"
    A.let_dig_hyp_pt  = "(" + A.let_dig + "|[.-])"
    A.let_dig_hyp_ptS = "(" + A.let_dig + "|[.-])+"
    A.let_dig_hyp     = "(" + A.let_dig + "|[-])"
    A.let_dig_hypS    = "(" + A.let_dig + "|[-])+"
    A.tstampEmpirical = ( A.Lets + "\s" +  A.digits + "\s" +
                          A.digits + ":" + A.digits  + ":" + A.digits )
    A.tstampEmpDpkg   = (  A.digits + "-" + A.digits + "-" + A.digits + "(\s|T)" +
                           A.digits + ":" + A.digits + ":" + A.decnum +  A.let + "?")

    syslogFldRexDict = {
        'HOSTNAME' : "(" + A.let_dig + A.let_dig_hyp_pt + "*" + A.let_digS + \
                     "|" + "\d+(\.\d+)*"
                     ")",                             # not compliant RFC
        'TIMESTAMP': ( "(" + A.tstampEmpirical +      # not compliant RFC:seen syslog
                       "|" + A.tstampEmpDpkg +        # not compliant RFC:seen dpkg.log
                       ")"
                     ),
        'NUM':   A.digits,
        'syslogtag': "[^:]+:",
        'bracket'  : '\[[^[]*\]',
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

    def parse(self, logline):
        "Parse log line "
        mobj =  self.builtRex.match(logline)
        data = self._logline_wrapper

        logging.debug( f"Parsing RFC5424 line:{repr(logline)}")

        try:
            if mobj :
                logging.info( f"RSyParsing({self.name}): Match for logline\n\t{logline}" +
                              f"\n\t{mobj.groupdict()}\n\t{mobj.span()}" )
                pdict = mobj.groupdict()
            else:
                logging.error(f"RSyParsing({self.name}): No match for logline\n\t{repr(logline)}")
                pdict = {}

            data.fieldnames = pdict.keys()
            data.clear()
            for k, v in pdict.items():
                data[k] = v

            logging.debug( f"\tParsed(type(parsed)):{pdict}")
            return data

        except ParseError as err:
            logging.error( f"RSyParsing({self.name})\t parse error:{err}")

        data.fieldnames = []
        data.clear()
        return data

#
# Here comes the parser for  RSYSLOG_TraditionalFileFormat style
#

class RSysTradiVariant(LogParser):
    """ Parser for  handle rsyslog RSYSLOG_TraditionalFileFormat;
        this is not a standard compliant parser, therefore the "Variant" in the class name.
"""

    def __init__(self, tableEntry):
        """ tableEntry will correspond to functions providing the tableEntry parm.
"""
        LogParser.__init__(self)
        self._logline_wrapper = LogLine()
        self.tableEntry = tableEntry
        spec  = RSyParsing.tmplDict[tableEntry]
        self.RSyParsing = RSyParsing( tableEntry, spec[0], spec[1])

    def parse(self, logline):
        "Parse log line "
        data = self._logline_wrapper

        logging.debug( f"Parsing RSysTradiVariant ({self.tableEntry}) line:{repr(logline)}")
        try:
            parsed = self.RSyParsing.parse(logline)
            logging.debug( f"**parsed = {type(parsed)}:\t{parsed}")
            pdict = parsed    # .as_dict()

            data.fieldnames = pdict.keys()
            data.clear()
            for k, v in pdict.items():
                data[k] = v

            logging.debug( f"\tParsed(type(parsed)):{pdict}")
            return data
        except ParseError as err:
            logging.error( f"RSysTradiVariant  ({self.tableEntry})\t parse error:{err}")

        data.fieldnames = []
        data.clear()
        return data

def FileFormat():
    return RSysTradiVariant("FileFormat")

def TraditionalFileFormat():
    return RSysTradiVariant("TraditionalFileFormat")

def ForwardFormat():
    return RSysTradiVariant("ForwardFormat")

def TraditionalForwardFormat():
    return RSysTradiVariant("TraditionalForwardFormat")

def DockerCLog():
    return RSysTradiVariant("DockerCLog")


# ................................................................................
#
# Version that uses dpath (extended version) to select fields or subtrees
# in the JSON representation. For details on available generalized keys,
# see test material, markdown documentation and documentation on
# dpath.
# ................................................................................


class JSONParserPlus(LogParser):
    """\
Parser implementation for JSON format logs, extended capabilities using
dpath to select with multilevel keys or regexps

Recall that the base class LogParser makes this class callable (applys method parse
to a line)
"""

    def __init__(self):
        LogParser.__init__(self)
        self._logline_wrapper = LogLine()

    def fe_returns_Json(self):
        "Indicate that this returns JSON"
        return True
        
    def parse(self, line):
        """Parse JSON line, allows multilevel keys with regexps"""
        try:
            parsed_row = json.loads(line)
            data = parsed_row
        except Exception as err:
            print(f"In {type(self)}.parse:\n\t{err}\n\tcould not parse JSON from:'{line}'",
                  file=sys.stderr)
            print(f"\ntype(line)={type(line)}", file=sys.stderr)
            data = {"raw":line}
            
        return data


def dpath_getter_gen(parser, fields, options=None):
    """\
Generator meta-function to return a function parsing a logline and returning
multiple options (tab-delimited)"""


    def dpath_getter_fun(line, parser, options, fields):
        data = parser(line)
        x = dpath.util.search(data, fields)
        logging.debug(f"In dpath_getter_fun:line={line},\tparser={parser},\toptions={options}," +
                      f"\tfields={fields}\treturning:{x}")
        return x

    return partial(dpath_getter_fun, parser=parser, options=options, fields=fields)


def dpath_getter_gen_mult(parser,  fields, options = None):
    """\
Generator meta-function to return a function parsing a logline and returning
multiple options (tab-delimited)

This version is prepared to handle cases where multiple keys are required,
in practice this would cover cases where we want to 'or' in ways constrained 
by dpath

It is not clear at this point that 2 functions are really needed!!!
"""
    print(f"In dpath_getter_gen_mult options={options}, fields={fields}", file=sys.stderr)
    def dpath_getter_mult_fun(line, parser, options, fields):
        data = parser(line)
        x = dpath.util.search(data, fields)
        logging.debug(f"In dpath_getter_fun:line={line},\tparser={parser},\toptions={options}," +
                      f"\tfields={fields}\treturning:{x}")
        return x

    return partial(dpath_getter_mult_fun, parser=parser, options=options, fields=fields)
