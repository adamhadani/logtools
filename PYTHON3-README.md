# Python-3 port

## TOC
<!--TOC-->

- [Python-3 port](#python-3-port)
  - [TOC](#toc)
  - [Note](#note)
    - [Intent and issues found](#intent-and-issues-found)
    - [Added functionality](#added-functionality)
    - [Test and operative environment](#test-and-operative-environment)
    - [Installation](#installation)
    - [First experiments](#first-experiments)

<!--TOC-->

## Note

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
  + Current versions are `sqlsoup 0.9.1` and  `SQLAlchemy 1.4.0b3`. 
  + This port has been made requiring specific older
    versions. It is highly recommended to operate under `virtualenv`; `
    setup.py`has been changed accordingly. 
  + A file [requirements.txt](./requirements.txt) has been added to document this, and
    can be used with `pip3`.
  
- the package's usage of `datetime.strptime` in my locale `"fr_FR.UTF-8"`was found
  problematic ( `testQps` <I>fails when parsing date</I> `11/Oct/2000:14:01:14 -0700`
  <I>which is fine in my locale</I>) : 
  disabled statements `locale.setlocale(locale.LC_ALL, "")`in 
  `_qps.py` and `_plot.py`. 
  The directory `aux` has been added with script `testStrptime.py` to test 
  under different locales.
  
- when experimenting the use of ̀logjoin` with `mysql`
  + installing the `PyMySQL` module proved tricky (On Linux/Ubuntu):
    1. pip3 install mysql-connector
	1. pip3 install PyMySQL
	1. needed to add the following in `__init__.py`:
	~~~
	import pymysql
    pymysql.install_as_MySQLdb()
	~~~
  + Note that SQLsoup documentation is found at
    1. https://sqlsoup.readthedocs.io/en/latest/
    1. https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine 
	
  + For connecting, the string form of the URL is 
     > dialect[+driver]://user:password@host/dbname[?key=value..], 
	 where 
	 + dialect is a database name such as mysql, oracle, postgresql, etc., and
	 + driver the name of a DBAPI, such as psycopg2, pyodbc, cx_oracle, etc. 
	 Alternatively, the URL can be an instance of URL.
     Example: `mysql://scott:tiger@hostname/dbname`

  + Getting error: `1193, "Unknown system variable 'tx_isolation'"`, which is not new:
    + https://github.com/sqlalchemy/sqlalchemy/issues/5161
	 > something about your MySQL server is not sending out a version detection string
	 > that is expected. Can you go to your MySQL console and send the results of:
     > SELECT VERSION()

   Conclusion:

	 > transaction_isolation was added in MySQL 5.7.20 as an alias for 
	 > tx_isolation, which is now deprecated and is removed in MySQL 8.0. 
	 > Applications should be adjusted to use transaction_isolation in preference
	 > to tx_isolation. PyMySQL/PyMySQL#614

    All of this looks like an incompatibility between my version of MySQL (8.xx) and
	the version of PyMySQL 

    I am probably stuck with SQLAlchemy and SQLsoup because of the problem at the top,
	probably not worth it using SQLAlchemy and SQLsoup... Or will need to upgrade
	these 2 things to versions current, compatible between them and with Mysql 8.0!!!

### Added functionality

   See [PYTHON3-ADDITIONS](./PYTHON3-ADDITIONS.md). 
   In [FORMAT-CHEATSHEET](./FORMAT-CHEATSHEET.md), some help for parser format selection


  
### Test and operative environment
 This is really setting up the development / maintenance environment:
 
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

 ### First experiments
 
 - configuration: 
   - establish a  `~/.logtoolsrc` file, which will used for setting 
     parameters or defaults
   - as configuration files are named in   `~/.logtoolsrc`, create and populate them,
     for empty files are OK if there is no blacklist:
```
touch bots_hosts.txt         # File designated in ~/.logtoolsrc
touch bots_useragents.txt    # File designated in ~/.logtoolsrc
 ```
	 
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
