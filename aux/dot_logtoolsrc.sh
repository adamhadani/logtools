#!/usr/bin/env bash


# This script prepares the ~/.logtoolsrc for testing, may evolve to be usable as
#      an example to be filled/modified, but for now  just a test thing
#
#  Arguments
#      1) first argument: PATH leading to logtools package source
#      2) second argument: path for ~/.logtoolsrc; default to ~/.logtoolsrc

arg2=$2
DESTFILE=${arg2:=/tmp/.logtoolsrc}

sed -e "s/BASEPATH/$1/" >"$DESTFILE" <<END
# ------------------------------------------------------------
# defaults for various parameters, organized per script
# ------------------------------------------------------------

[filterbots]
 bots_ua: BASEPATH/logtools/data/examples/bots_useragents.txt
 bots_ips: BASEPATH/logtools/data/examples//bots_hosts.txt
 ip_ua_re: ^(?P<ip>.*?) -(?:.*?"){5}(?P<ua>.*?)"


[logtail]
field: 2

# ------------------------------------------------------------
# this file is read by  configparser (python)
#       doc : https://docs.python.org/3/library/configparser.html
#
# this allows for comment lines !!
#
# The general format of the file is inspired by Microsoft's INI
# ------------------------------------------------------------
END

echo Produced file $DESTFILE

