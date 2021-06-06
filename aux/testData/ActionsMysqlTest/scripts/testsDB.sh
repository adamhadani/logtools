#!/usr/bin/env bash

# ------------------------------------------------------------------------------
#
# This script is installed in /aux/testData/ActionsMysqlTest/scripts
# and is used to run Mysql DB tests on Github Actions hosted VM
#
# The available docker images in the VM used are listed at bottom
# ------------------------------------------------------------------------------

ECHO=""

# exit upon first error in pipes etc.
set -e

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
    return 0
}


# this is the test command
function doTestByName () {
    testNm=$1
    case ${testNm} in

        DB2) docker image inspect ubuntu | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	     ;;

        # the following DB2* test several syntaxes for selecting in -logjoin
        DB2a) docker image inspect ubuntu |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "*/0/RepoTags" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	      ;;

	# here we have multiple keys, see how we want this to pan out (extension??)
        DB2b) docker image inspect ubuntu |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "**/{RepoTags|Created}" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	      ;;

	# here we hve an empty key, then we will need to define desirable behaviour
        DB2c) docker image inspect ubuntu |
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP"  |  \
	     logjoin -f "**/Zorro" --frontend JSONParserPlus \
    	                --join-remote-key application \
    	                -F date,application,priority ${DEBUGLEVEL}
	     ;;

        # same as DB3W, uses the non ORM backend using flag --backend
	DB3w) docker image inspect ubuntu | \
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
	DB3W) docker image inspect ubuntu | \
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
	DB3WW) docker image inspect ubuntu | \
	     wrapList2Json.py | \
	     logparse --parser JSONParserPlus -f "TOP" | \
	     logjoin -f "**/RepoTags" --frontend JSONParserPlus \
    	                 --join-remote-key "-" \
			 --join-remote-name EventTable \
    	                 -F user_id,application,message ${DEBUGLEVEL}
	       ;;

	# test/demo the logdb capabilities
	#
	DBOP1) docker image inspect ubuntu | \
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

	sDBJ) msg "testing Logjoin with database"
	    tset=( DB2 DB2a DB3w DB3W DB3WW)
	    ;;

	sDBOP) msg "testing Logdb with database operations (insertion)"
	    tset=( DBOP1 DBOP2)
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

# ---------------------------------------------------------------------
# docker images available in VM (observed 6/5/21)
# ---------------------------------------------------------------------
#
# REPOSITORY       TAG         IMAGE ID       CREATED       SIZE
#
# ubuntu           16.04       9ff95a467e45   2 weeks ago   135MB
# ubuntu           18.04       81bcf752ac3d   2 weeks ago   63.1MB
# node             14          9153ee3e2ced   3 weeks ago   943MB
# node             14-alpine   8e69714aa82b   3 weeks ago   117MB
# node             12          d2035012c0a2   3 weeks ago   917MB
# buildpack-deps   stretch     c7dc37a15db1   3 weeks ago   835MB
# buildpack-deps   buster      827c35559861   3 weeks ago   804MB
# debian           9           acf04b8ccc37   3 weeks ago   101MB
# debian           10          4a7a1f401734   3 weeks ago   114MB
# ubuntu           20.04       7e0aa2d69a15   6 weeks ago   72.7MB
# node             10-alpine   aa67ba258e18   7 weeks ago   82.7MB
# node             12-alpine   deeae3752431   7 weeks ago   88.9MB
# alpine           3.11        e389ae589224   7 weeks ago   5.61MB
# alpine           3.12        13621d1b12d4   7 weeks ago   5.58MB
# alpine           3.13        6dbb9cc54074   7 weeks ago   5.61MB
# node             10          28dca6642db8   8 weeks ago   910MB
# ---------------------------------------------------------------------
#
