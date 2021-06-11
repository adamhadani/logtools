#!/usr/bin/env bash


# This script prepares the ~/.logtoolsrc for testing, when using SQLite,
#
#  Arguments
#      1) first argument: PATH leading to logtools package source
#      2) second argument: path for ~/.logtoolsrc; default to ~/.logtoolsrc
#      3) third argument: path for ~/.logtools.d
#      4) fourth argument: path of the SQLite file
BASEPATH="$1"
arg2="$2"
arg3="$3"
arg4="$4"
DESTFILE="${arg2:=/tmp/.logtoolsrc}"
DESTDIR="${arg3:=/tmp/.logtools.d}"
sqlite_file="${arg4:=/tmp/sqlite_file.db}"

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

   ## these are the connect parameters of sqlalchemy instantiation
   ## for information on connect string, see
   ## https://docs.sqlalchemy.org/en/13/dialects/sqlite.html\
   ##         #module-sqlalchemy.dialects.sqlite.pysqlite
   ##
   ## possible sqlite_file path may be absolute or relative:  
join_connect_string: sqlite:///${sqlite_file}

join_remote_fields: *
join_remote_name: testTable
join_remote_key: -


[dbOp]  
field: 1
frontend:

dbOperator: SQLAlcDbOp

    ## see above 
dbOp_connect_string: sqlite:///${sqlite_file}

dbOp_remote_fields: *
dbOp_remote_name: testTable
dbOp_remote_key: -


[RSysTradiVariant]
file: ${HOME}/.logtools.d/tradivariantParsing.txt


END

echo Produced file $DESTFILE
# reset umask
$maskOrig

if [ ! -d ${DESTDIR} ] ; then
    mkdir -p ${DESTDIR}
    echo Created dir  ${DESTDIR}
fi

cat >${DESTDIR}/tradivariantParsing.txt <<EOF
#$template TestA,"%HOSTNAME%"

#$template TestB,"%HOSTNAME%\n"

#$template TFFA,"%TIMESTAMP% %HOSTNAME%\n"
#$template TFFB,"%TIMESTAMP% %HOSTNAME% %syslogtag%"
#$template TFFC1,"%TIMESTAMP%"

EOF

echo Produced file ${DESTDIR}/tradivariantParsing.txt
