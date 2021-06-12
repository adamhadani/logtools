#!/usr/bin/python3

import os
import sys
import locale
import argparse
import traceback

from collections.abc import Iterable

from datetime import datetime
import pandas as PAN


def testDates(locKey):
   "Check datetime.strptime using data in global table; show effects of locale"
   if locKey  not in errDict:
      errDict[locKey] = 0
   for strDte, fmt, val in testDatesTb:
      try : 
          t = datetime.strptime( strDte, fmt)
      except Exception as err:
          print(f"Unable to recover date from '{strDte}'\n\tformat:'{fmt}'" ,
                file=sys.stderr)
          errDict[locKey] += 1
      else:
          print( strDte, fmt, val, t)
          
def testDateMain():
   "Check datetime.strptime for locales in global table testLocales"
   print( f"Default locale" )
   testDates(None)
   print( f"... default "+ ". "*30 +"\n" )

   for loc in testLocales:
       print( f"Setting locale: {loc}" )
       locale.setlocale(locale.LC_ALL, loc)
       testDates(loc)
       print( f"... {loc:12s} "+ ". "*30 +"\n" )

   print( f"Error summary\n\t{errDict}")


def localeAttribs(loc):
    "Collect attributes of locale"
    locale.setlocale(locale.LC_ALL, loc)
    lcDict = locale.localeconv()
    for x in locKeys:
       lcDict[ x[1] ] =  locale.nl_langinfo(x[0])
    rDict = {}
    for k in lcDict:
       v = lcDict[k]
       if not isinstance(v,str) and isinstance(v, Iterable):
          rDict[k] = [ "[ " + ", ".join( map ( str, v)) + "]" ]
       else:
          rDict[k] = [v]
    return rDict

#
# Note the reason for putting dictionnary values in lists (as above) is described
#  in https://stackoverflow.com/questions/57631895/dictionary-to-dataframe-error-if-using-all-scalar-values-you-must-pass-an-ind
#
 
def testLocaleAttr():
    "Collect locale attributes for a set of locale in global table testLocales"
    dfList = []
    for loc in testLocales:
        attrs = localeAttribs(loc)
        attrs["LOCALE"] = loc
        df = PAN.DataFrame(data = attrs).transpose()
        dfList.append( df )
    dfGlob = PAN.concat(dfList, axis  = 1 )
    dfGlob.columns = dfGlob.loc["LOCALE",:]
    df1 = dfGlob.drop("LOCALE", axis = 0)
    return df1
 
if __name__ == '__main__':
    description =""" 
    This program performs a check on the ability to extract date and time using
    strptime depending on the locale configuration. Also, it documents some
    of the attributes customized by setting locale.
    """

    testDatesTb= ( ('10/Oct/2000:13:57:01', '%d/%b/%Y:%H:%M:%S', None),
                   ('10/Oct/2000:13:57:01 -0700', '%d/%b/%Y:%H:%M:%S -0700', None)
                )

    testLocales= ( "", "fr_FR.UTF-8", "en_US.UTF-8", "en_GB.UTF-8",  "C")

    errDict = {}

    locKeys= (
        (locale.D_T_FMT, 'locale.D_T_FMT'),
        (locale.CODESET, 'locale.CODESET'),
        (locale.D_FMT,   'locale.D_FMT'),
        (locale.T_FMT,   'locale.T_FMT'),
        (locale.T_FMT_AMPM, 'locale.T_FMT_AMPM'))


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
        
        argLineParser.add_argument("-c","--check" ,action="store_true",
                                  dest="doCheck",
                                  help="Checks ability to read time for data and formats in internal table")
        argLineParser.add_argument("-p","--print" ,action="store_true",
                                  dest="doPrint",
                                  help="Prints customizable attributes for a set of locales in internal table")

        try:
            options = argLineParser.parse_args()
            if options.doDebug:
                sys.stderr.write (f"options:{repr(options)}\n")

            if options.doCheck:
                testDateMain()
            if options.doPrint:    
                print( testLocaleAttr() )


        except Exception:
            sys.stderr.write ( "Quitting because of error(s)\n" )
            traceback.print_exc()
            sys.exit(1)
           

    mainPgm()

    
