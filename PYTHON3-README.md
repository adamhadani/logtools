# Python-3 port

## TOC
<!--TOC-->

- [Python-3 port](#python-3-port)
  - [TOC](#toc)
  - [Notes](#notes)
    - [Intent and issues found](#intent-and-issues-found)
    - [Moving to sqlalchemy](#moving-to-sqlalchemy)
  - [Added functionality](#added-functionality)
  - [Test and operations](#test-and-operations)
    - [Test and operative environment](#test-and-operative-environment)
    - [Installation](#installation)
    - [First experiments](#first-experiments)

<!--TOC-->

## Notes

These are short notes documenting the Python-3 port, which is still to
be considered experimental.

### Intent and issues found

The idea was to do a straightforward port to Python-3, since I wanted to
use the package with the native Python-3 on my Ubuntu 20.10 Linux.

Following issues were encountered:

- parts concerning `geoIP` have not been ported or tested, therefore are deemed
  not functional

- the `sqlsoup` package uses features of `SQLAlchemy`  ( `MapperExtension` ) which have 
  been deprecated (then suppressed since version 0.7; see
  https://docs.sqlalchemy.org/en/13/orm/deprecated.html ).
  + Workable but abandonned (after `commit f63db028b5f14cd2aa` on May 5, 2021) story:
    + Current versions are `sqlsoup 0.9.1` and  `SQLAlchemy 1.4.0b3`. 
    + Make the port to require specific older
      versions. This suggests operate under `virtualenv`; ` setup.py` had been changed
	  accordingly. 
    + A file [requirements.txt](./requirements.txt) has been added to document this, and
      can be used with `pip3`.
  + Current approach:
    + Removed all `SQLsoup` dependencies
	+ Used `SQLAlchemy` instead (`version >= 1.4.13`)
	+ Attempting to use the higher abstraction ORM, for query preparation and
	  possibly exploitation. 
  
- the package's usage of `datetime.strptime` in my locale `"fr_FR.UTF-8"`was found
  problematic ( `testQps` <I>fails when parsing date</I> `11/Oct/2000:14:01:14 -0700`
  <I>which is fine in my locale</I>) : 
  disabled statements `locale.setlocale(locale.LC_ALL, "")`in 
  `_qps.py` and `_plot.py`. 
  The directory `aux` has been added with script `testStrptime.py` to test 
  under different locales. Multiple locales where tested in the CI (mostly
  Github's Actions framework)
  
- when experimenting the use of ̀logjoin` with `mysql`
  + installing the `PyMySQL` module proved tricky (On Linux/Ubuntu):
    1. pip3 install mysql-connector
	1. pip3 install PyMySQL
	1. needed to add the following in `__init__.py`:
	~~~
	import pymysql
    pymysql.install_as_MySQLdb()
	~~~
	
  + For connecting, the string form of the URL is 
     > dialect[+driver]://user:password@host/dbname[?key=value..], 
	 
     Example: `mysql://scott:tiger@hostname/dbname`
	 where 
	 + dialect is a database name such as mysql, oracle, postgresql, etc., and
	 + driver the name of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. 
	 + Alternatively, the URL can be an instance of URL class.
     + this parameter may be set in ~/.logtoolsrc

  + this is required when using SQLAlchemy

  + Finally decided to use an up to date version of SQLAlchemy to handle 
     MySQL (8.xx). Updated version of PyMySQL: see above about package selection 


### Moving to sqlalchemy

1. Documentation for sqlalchemy: https://docs.sqlalchemy.org/en/14/index.html 
  + a more tutorial thing at 
    https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls
	
1. Used SQLAlchemy as follows:
   + minor support of Core tools sufficient to run logjoin
   + more extensive support of ORM, in logjoin and logdb (added). 
   + ORM to be prioritized for future developments
   
   + only tested with mysql as database server.

## Added functionality

   See [PYTHON3-ADDITIONS](./PYTHON3-ADDITIONS.md). 
   In [FORMAT-CHEATSHEET](./FORMAT-CHEATSHEET.md), some help for parser format selection

## Test and operations
  
### Test and operative environment
 This is really setting up the development / maintenance environment; I developped
 the habit to use virtualenv with precisely versionned Python packages when 
 trying to operate with SQLSoup, since this entailed compatiblility issues. 
 It is probably not necessary now.
 
 - setup a `virtualenv`environment, requiring Python 3.8.6, ( or whatever version 
   you want to use.  Python 3.8.6 happens to be the native Python-3 on my system,
   with which all development and tests have been done: 
   ```
   cd <py3port-dir>
   virtualenv -p 3.8.6 .
   ``` 
 - populate it according to [requirements.txt](./requirements.txt) 
 - development and maintenance of the package are all performed under this environment
 
### Installation
 
 This may be done as follows:

 - setup <I>or activate</I> the `virtualenv` environment using the 
   [requirements.txt](./requirements.txt) file.
 - change directory to the package (where `setup.py` and source code are found)
 - run `setup.py` using the python interpreter in the `virtualenv` environment:
 
  
```
   # establish virtualenv
   . venvSandBox/bin/activate
   # keep track of wd and cd to source
   v=`pwd`
   pushd ~/src/logtools/
   # install proper
   $v/venvSandBox/bin/python3 setup.py install
```

 
### Configuration 
   - establish a  `~/.logtoolsrc` file, which will used for setting 
     parameters or defaults. There are many fields needed from this configuration,
	 some of which can be overriden from the command line.
	 + for doing this, a model can be found in aux/dot_logtoolsrc.sh, which 
	   creates test configuration file(s) for CI in Github's Action system
   - For the following configuration files, named in   `~/.logtoolsrc`, create and populate them,
     empty files are acceptable if there is no blacklist:
```
touch bots_hosts.txt         # File designated in ~/.logtoolsrc
touch bots_useragents.txt    # File designated in ~/.logtoolsrc
 ```


### First experiments

 - `filterbots`: 
   1. extract log entries corresponding to some ̀sudo` uses. <I>Notice that 
   we are using the `-s` flag to define the level of output</I>
 ```
gunzip --stdout /var/log/auth.log.*.gz | \
cat /var/log/auth.log -  | \
filterbots -s ERROR -r ".*sudo:(?P<ua>[^:]+).*COMMAND=(?P<ip>\S+).*"  --print
 ```
 
  - filter :
  
  
  - `logmerge`
     1. Merges several logs sorting a field defined by delimiter (1 char) and field number:
          ```  
          logmerge -d'-' -f1 /var/log/auth.log /var/log/syslog | \
          grep -i upload
          ```
  
     2. Use a parser for merging 
	    -  the following supposes Apache Common Log Format
          see http://httpd.apache.org/docs/1.3/logs.html#accesslog), examples shown in
		  [MORE-DOC.md](./MORE-DOC.md) :
          ```
           logmerge --parser CommonLogFormat -f4 /var/log/auth.log /var/log/syslog
           ```
        - by default `format='%h %l %u %t "%r" %>s %b'`

   - `logparse` 
      1. Parses according to parser format, select output field: 
	     <I>example extracts the date-time)</I>:
         ```
           cat testData/testCommonLogFmt.data | logparse --parser CommonLogFormat  -s INFO -f4
	     ```
		 
	  2. Same, selects multiple fields, <I> for some reason only 1 line is output</I>
	   
         ```
		 cat  testData/testCommonLogFmt.data| logparse --parser CommonLogFormat  -s DEBUG -f1,4
         ```
		 
      3. Added RFC 5424 parser `SyslogRFC5424`, here ̀-f`supports symbolic field selection 

         ```
         cat testData/testRFC5424.data | logparse --parser SyslogRFC5424 -f hostname -s INFO
         ```
		 
		 Field names can be found running with flag `-s DEBUG`

      4. Added a facility to handle logs specified by "traditional templates" in the style
         defined at url https://rsyslog-5-8-6-doc.neocities.org/rsyslog_conf_templates.html.
		 Usable with /var/log/{syslog,kern.log,auth.log}.
		 ```
		 cat testData/TestAuth.data  | \
		     testLogparse --parser TraditionalFileFormat -f TIMESTAMP -s ERROR	
		 ```
         Among capabilities, handle Docker log format:
		 
		 ```
		 docker container logs mysql1  2>/dev/stdout >/dev/null| head -2| \
		 testLogparse  --parser   DockerCLog --raw \
		               -f TIMESTAMP,NUM,bracket,bracket1,bracket2,msg  -s ERROR
		 ```
		 where DockerCLog is defined in parsers2.py, but could also be supplied
		 via configuration file in section `RSysTradiVariant`, outputs
					   
		 ```
	     2021-04-26T...Z	0	[System]	[MY-010116]	[Server]	.../mysqld () starting ...
         2021-04-26T...Z	1	[System]	[MY-013576]	[InnoDB]	InnoDB initialization start	
		 ```
		
	  5. Added `logdb`, performing more database operations from logs:				   

         As an example, exploiting docker's inspect output 

         ~~~
         docker image inspect nginx | \
	     wrapList2Json.py | \
	     testLogparse --parser JSONParserPlus -f "TOP" | head -1 | \
	     testLogdb -f "TOP/*/{RepoTags|Config}/{Env}" --frontend JSONParserPlus \
    	                 --join-remote-key "application" \
			             --join-remote-name EventTable 
         ~~~ 
   
		 Enters the following in the database, which is reminiscent of "Triple Store" for
		 RDF, and borrows ideas from `SQLAlchemy/example/code/adjacencyList.py`
		 
         ~~~
         id,parent_id,name,nval
         1000,NULL,RootNode,2021-05-17T15:10:25.642125
         1001,1000,RangeStart,1010
         1010,1000,**TOP**,TREEPOS.LIST
         1011,1010,0,TREEPOS.TOP
         1012,1011,Driver,default
         1013,1011,Options,TREEPOS.EMPTY_TREE
         1014,1011,Config,TREEPOS.LIST
         1015,1014,0,TREEPOS.TOP
         1016,1015,Subnet,172.19.0.0/16
         1017,1015,Gateway,172.19.0.1
         1018,1010,1,TREEPOS.TOP
         1019,1018,4cf07fa937da4b6ad844b3a6ca22a8eb167dc503544becda8789774a6e605c5b,TREEPOS.TOP
         1020,1019,Name,mysql1
         1021,1019,EndpointID,7edb7b1e866957f0de6150c73c78b70717a6bb833794009509f1002dec622f41
         1022,1019,MacAddress,02:42:ac:13:00:02
         1023,1019,IPv4Address,172.19.0.2/16
         1024,1019,IPv6Address,
         1025,1018,517acb5295aba5cc347d7aae88b525abf7faef26f5c481f2b82636b0619a192b,TREEPOS.TOP
         1026,1025,Name,mysql-workbench
         1027,1025,EndpointID,5255215cc33826d3b90973aaed786d3b3e2b620ddbe6a837c6ae060fc8ce61e4
         1028,1025,MacAddress,02:42:ac:13:00:03
         1029,1025,IPv4Address,172.19.0.3/16
         1030,1025,IPv6Address,
         1031,1000,RangeEnd,1030
          ~~~

		 
