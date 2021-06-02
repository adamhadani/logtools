#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# This script is installed in aux/scripts and is used to run Mysql DB tests
# on Github Actions hosted VM
# ------------------------------------------------------------------------------

ECHO=""

function usage() {
    cat >/dev/stderr <<EOF
usage testDB.sh [-d][-h][-v][-t testname][-s testSetName]

Arguments:
    -h       : print this help
    -d       : debug mode, only echo commands, implemented by local var DEBUGLEVEL
    -v       : verbose
    -t  xx   : execute test xx 
    -s  xx   : execute test set xx
EOF

    exit 0
    }


function checkEnv () {
    # this function is used in the development version 
}


# this is the test command
function doTestByName () {
    testNm=$1
    case ${testNm} in
        Ef2)  dockerFinder.py -I  idba -n nginx --fmt json| \
    	     logparse --parser JSONParserPlus -f "{attrs}" | \
    	     logjoin -f 1 ${DEBUGLEVEL}
    	     # OK
    	;;
        Ef3)  dockerFinder.py -I  idba -n nginx --fmt json| \
    	     logparse --parser JSONParserPlus -f "{attrs}" | \
    	     logjoin -f 0 ${DEBUGLEVEL}
    	     # OK
    	;;
	
        #  ..................................................
        #  recall that currently we have the following fields in the DB table XXXX TBD
    	#  Field,Type,Null,Key,Default,Extra
    	#  idtestTable,int,NO,PRI,NULL,
    	#  date,date,YES,,NULL,
    	#  application,varchar(45),YES,,NULL,
    	#  priority,varchar(45),YES,,NULL,
    	#  Message,varchar(255),YES,,NULL,
            #  ..................................................
        Ef4)  dockerFinder.py -I  idba -n nginx --fmt json| \
    	     logparse --parser JSONParserPlus -f "{attrs}" | \
    	     logjoin -f 0 -F 'date,application,priority' \
			 ${DEBUGLEVEL}
                 # OK
    	  ;;
        Ef5)  dockerFinder.py -I  idba -n nginx --fmt json| \
    	     logparse --parser JSONParserPlus -f "{attrs}" | \
    	     logjoin -f 0 -F '*' \
			 ${DEBUGLEVEL}
                # OK
    	  ;;

        DB1) dockerFinder.py -I  idba -n nginx --fmt json | \
	     logparse --parser JSONParserPlus -f "{attrs}" | \
	     logjoin -f attrs/RepoTags --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
    	 # OK
	     ;;

        DB2) docker image inspect nginx | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	     ;;
	
        # the following DB2* test several syntaxes for selecting in -logjoin
        DB2a) docker image inspect nginx |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "*/0/RepoTags" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	      ;;
	
	# here we have multiple keys, see how we want this to pan out (extension??)
        DB2b) docker image inspect nginx |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "**/{RepoTags|Created}" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	      ;;
	
	# here we hve an empty key, then we will need to define desirable behaviour
        DB2c) docker image inspect nginx |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "**/Zorro" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	     ;;

        # same as DB3W, uses the non ORM backend using flag --backend
	DB3w) docker image inspect nginx | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
			 --backend sqlalchemyV0 \
    	                 --join-remote-key application \
			 --join-remote-name EventTable \
    	                 -F user_id,application,message ${DEBUGLEVEL} 
	     ;;

	
	# these are intended for exploring the V2 / ORM based version
	# backend specified in ~/.logtoolsrc
	DB3W) docker image inspect nginx | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
    	                 --join-remote-key application \
			 --join-remote-name EventTable \
			 --delimiter " -- " \
    	                 -F user_id,application,message ${DEBUGLEVEL}
	     ;;

        # test suppression of the where clause, otherwise it is the same
	# in practice this uses metadata loaded from server, and tests it 
	DB3WW) docker image inspect nginx | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
    	                 --join-remote-key "-" \
			 --join-remote-name EventTable \
    	                 -F user_id,application,message ${DEBUGLEVEL}
	       ;;

	# test/demo the logdb capabilities
	#
	DBOP1) docker image inspect nginx | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" |  \
	     logdb -f "TOP/*/{RepoTags|Config}/{Env}" --frontend JSONParserPlus \
    	                 --join-remote-key "application" \
			 --join-remote-name EventTable \
    	                  ${DEBUGLEVEL}
	     ;;

	DBOP2) docker  network inspect mysql-docker-net | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" |  \
	     logdb -f "**/{Containers|IPAM}" --frontend JSONParserPlus \
    	                 --join-remote-key "application" \
			 --join-remote-name EventTable \
    	                  ${DEBUGLEVEL}
	     ;;
	
        *)
    	echo parameter testNm=${testNm} not accepted
    	exit 1
    	
    esac
    r=$?
    echo returned $r >/dev/stderr
    return $r
}


function msg() {
    echo "$1" >/dev/stderr
    }

function doTestSet () {
    testSetNm=$1
    case  "${testSetNm}" in
	sA) msg "testing logparse with prerecorded json from docker"
	    tset=( 1 2 3 )
	    ;;
	sB) msg "testing logparse with docker JSON from dockerFinder, requires [~/].dockerTools.cfg"
	    tset=( a A AA c C )
	    ;;

        sC) msg "testing logjoin with docker JSON from dockerFinder,  requires [~/].dockerTools.cfg"
            tset=( D E  Ef2 Ef3 Ef4 Ef5 Ef6 F1b F1c FL FS FS1 )
	    ;;

	sDBJ) msg "testing Logjoin with database"
	    tset=( DB1 DB2 DB2a DB3w DB3W DB3WW)
	    ;;
	
	sDBOP) msg "testing Logdb with database operations (insertion)"
	    tset=( DBOP1 )
	    ;;
	
	sBad) msg "These are the problematic tests, in some cases inconsistent flags..."
	      tset=( Ef1 F F1 FJ DB2b DB2c )
	      ;;
	
	*) echo "incorrect test set name: ${testSetNm}" >/dev/stderr
	   exit 3
    esac

    for t in ${tset[@]} ; do
	echo "** Entering test ${t} **"	    
	doTestByName ${t}
	echo "** Test ${t} returned $? **"
	echo ""
    done
}


# check that the environment is OK, main reason is to avoid wasting time on
# inconsistencies
checkEnv

set -e

while getopts "dhvt:s:" opt ; do

    case "$opt" in
    d)  verbose=1 ;
        DEBUGLEVEL="--sym DEBUG"
        ECHO=echo 	    
        ;;
    h|\?)
        usage
        ;;
    v)  verbose=1
        ;;

    t) doProc=testSingleName
       testName=$OPTARG
       ;;

    s) doProc=testSet
       testSetName=$OPTARG
       ;;

    
   *)  # redundant clause if getopts is totally selective
	echo Incorrect argument "$opt" >/dev/stderr
	exit 2
    esac

done

case ${doProc} in
    testSingleName)
	doTestByName ${testName}
	;;
    testSet)
	doTestSet ${testSetName}
	;;
    *)
	echo bad selector ${doProc}: error command line syntax
	usage
	exit 1

esac;


