#!/usr/bin/env bash


# This script prepares :
#    a file with MYSQL database privileges (with secret stuff), probably poorly located
#    in aux/testData (TBD!!) by generating a shell script and rewriting the privilege
#    file

#  Arguments
#      1) second arg: full path of SQL file with privilege values
#      2) : path of .cnf file for root with password
#      3) : path of .cnf file for root with default password
#      4) : path of .cnf file for user with password
arg2="$1"
rootCNF="$2"
rootCNFDefault="$3"
userCNF="$4"
DESTFILE="${arg2:=${HOME}/aux/testData/ActionsMysqlTest/scripts/rewstartCreateUserw.sh}"

echo "In mysql_config.sh"
echo "   entering USER DB passwd via environment variable USER_DB_PASS"

# Keep this file for myself
maskOrig=$(umask -p)
umask 0077
cat  >"$DESTFILE" <<END
/* 
 *    Administrative setup of Mysql server, for testing when running a server
 *    on a Github Actions VM. 
 *    
 *    This assumes that we are starting/configuring  the Default MySQL, which
 *    may be installed and started by Github Actions, with port is 3306.
 *    Details https://github.com/mirromutth/mysql-action#the-default-mysql, 
 *    docker images (plus info on running) at https://hub.docker.com/_/mysql.
 * 
 *    Available packages in Github VMs are described at  
 *    https://github.com/actions/virtual-environments, from which
 *    ubuntu-latest is accessible at 
 *    https://github.com/actions/virtual-environments/blob/main/images/linux/Ubuntu2004-README.md
 * 
*/

/* This creates the user(s) and their privileges when sourced as mysql 'root' .
 *  This file is located at on development host  and in loaded VM: 
 *  - aux/testData/ActionsMysqlTest/mysql/startCreateUser.sql 
 *  
 *    '**USERPASS**' has been substituted by using the Github.secrets mechanism
 *    '**ROOTPASS**' has been substituted by using the Github.secrets mechanism
*/

/* This assumes that the user running the script effectively has the Mysql rootpass
   set up by default for the Mysql server in the Github VM; now it will be changed
   according to the secret:
*/

ALTER USER 'root'@'localhost' IDENTIFIED BY  '${ROOT_DB_PASS}';

/* Found experimentally that 'root'@'127.0.0.1 does not exist in the reference Mysql, 
 * as set up by Github. I tend to prefer to have both versions (localhost and 127.0.0.1)
*/
CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '${ROOT_DB_PASS}';
FLUSH PRIVILEGES;

CREATE USER 'user'@'localhost'  IDENTIFIED BY '${USER_DB_PASS}';
CREATE USER 'user'@'127.0.0.1'  IDENTIFIED BY '${USER_DB_PASS}';


/* This creates a DB that user user cares about; all tables for this test in this DB */
CREATE DATABASE logfromtool;

GRANT ALL PRIVILEGES ON logfromtool.*  TO 'user'@'localhost';
GRANT ALL PRIVILEGES ON logfromtool.*  TO 'user'@'127.0.0.1';

FLUSH PRIVILEGES;

/* Show the situation */
SELECT host,user FROM mysql.user;

END

echo "Produced script file $DESTFILE, containing secret passwords"

cat >"$rootCNF" <<EOF
# This is for user root once configured
#
[client]
password=${ROOT_DB_PASS}

# See:
# 6.1.2.1 End-User Guidelines for Password Security
EOF
echo "Produced script file $rootCNF, containing secret root password"

cat >"$rootCNFDefault" <<EOF
# This is the default provided for root
[client]
password=${ROOT_ORIG_DB_PASS}

# See:
# 6.1.2.1 End-User Guidelines for Password Security
EOF
echo "Produced script file $rootCNFDefault, containing not so secret root original password"


cat >"$userCNF" <<EOF
[client]
password=${USER_DB_PASS}

# See:
# 6.1.2.1 End-User Guidelines for Password Security
EOF
echo "Produced script file $userCNF, containing secret user password"


# reset umask
$maskOrig
