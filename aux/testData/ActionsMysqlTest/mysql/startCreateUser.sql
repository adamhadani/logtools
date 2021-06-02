/* 
 *    Administrative setup of Mysql server, for testing when running a server
 *    on a Github Actions VM
 *
 *   (C) Alain Lichnewsky, 2021
*/

/* This creates the user(s) and their privileges when sourced as mysql 'root' .
 *  This file is located at on development host  and in loaded VM: 
 *  - aux/testData/ActionsMysqlTest/mysql/startCreateUser.sql 
 *  
 *  - it is expected that the 'secrets' mechanism will be used to substitute
 *    '**USERPASS**', and possibly '**rootpass**'
*/

/* Before do (with appropriate **rootpass** ) :
   The subnet value permits some flexibility in setting up the Docker network
     CREATE USER 'root'@'172.17.0.0/255.255.255.0' IDENTIFIED BY '**rootpass**';
     GRANT ALL PRIVILEGES ON *.* TO 'root'@'172.17.0.0/255.255.255.0';
*/

CREATE USER 'alain'@'localhost'  IDENTIFIED BY '**USERPASS**';
CREATE USER 'alain'@'127.0.0.1'  IDENTIFIED BY '**USERPASS**';

/* This creates a DB that user alain cares about */
CREATE DATABASE logfromtool;

GRANT ALL PRIVILEGES ON logfromtool.*  TO 'alain'@'localhost';
GRANT ALL PRIVILEGES ON logfromtool.*  TO 'alain'@'127.0.0.1';

/* Show the situation */
SELECT host,user FROM mysql.user;
