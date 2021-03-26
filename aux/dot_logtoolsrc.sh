#!/usr/bin/env bash


# This script prepares the ~/.logtoolsrc for testing, may evolve to be usable as
#      an example to be filled/modified, but for now  just a test thing
#
#  Arguments
#      1) first argument: PATH leading to logtools package source
#      2) second argument: path for ~/.logtoolsrc; default to ~/.logtoolsrc

BASEPATH="$1"
arg2="$2"
DESTFILE="${arg2:=/tmp/.logtoolsrc}"

echo "In dot_logtoolsrc.sh"
echo "   substituting : $BASEPATH to \$BASEPATH, emitting $DESTFILE"


cat  >"$DESTFILE" <<END
# ------------------------------------------------------------
# defaults for various parameters, organized per script
# ------------------------------------------------------------

[filterbots]
 bots_ua: ${BASEPATH}/data/examples/bots_useragents.txt
 bots_ips: ${BASEPATH}/data/examples//bots_hosts.txt
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

