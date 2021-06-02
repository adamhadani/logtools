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
echo "   entering USER DB passwd via environment variable"

# Keep this file for myself
maskOrig=$(umask -p)
umask 0077
cat  >"$DESTFILE" <<END
# ------------------------------------------------------------
# defaults for various parameters, organized per script
# ------------------------------------------------------------
# this file is read by https://docs.python.org/3/library/configparser.html
# which handles comment lines !!
#
# The general format of the file is inspired by Microsoft's INI
# ------------------------------------------------------------

[filterbots]
 bots_ua: ${BASEPATH}/data/examples/bots_useragents.txt
 bots_ips: ${BASEPATH}/data/examples//bots_hosts.txt
 ip_ua_re: ^(?P<ip>.*?) -(?:.*?"){5}(?P<ua>.*?)"


#Disable warnings about dpath standard versions that do not deal with 're' regexps
#[dpath]
#no-dpath-warning: True

[logtail]
field: 2


[logparse]
field: 1
raw:

[logjoin]  
field: 1
backend: sqlalchemy

   # for now used in logjoin only, if non void, filter output with
   # unicodedata.normalize(XXXX, str(x)).encode('ascii','ignore') where XXXX may be
   #  ‘NFC’, ‘NFKC’, ‘NFD’, and ‘NFKD’.
   #  -- for backward compatibility, enter 'NFKD' or leave this empty
   #  -- to suppress encoding enter 'None'
output_encoding: None

frontend:

   ## here we expect an rfc1738 URL
   ## these are the connect parameters of sqlalchemy instantiation
   ## USER_DB_PASS is a secret that needs to be properly substituted
join_connect_string: mysql://user:${USER_DB_PASS}@localhost/logfromtool

join_remote_fields: *
join_remote_name: testTable
join_remote_key: -


[dbOp]  
field: 1
frontend:

dbOperator: SQLAlcDbOp

   ## here we expect an rfc1738 URL
   ## these are the connect parameters of sqlalchemy instantiation   
join_connect_string: mysql://user:${USER_DB_PASS}@localhost/logfromtool

dbOp_remote_fields: *
dbOp_remote_name: testTable
dbOp_remote_key: -


[RSysTradiVariant]
file: ${HOME}/.logtools.d/tradivariantParsing.txt


END

echo Produced file $DESTFILE
# reset umask
$maskOrig
