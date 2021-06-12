
# Additional features in Python-3 port

## TOC
<!--TOC-->

- [Additional features in Python-3 port](#additional-features-in-python-3-port)
  - [TOC](#toc)
  - [Note](#note)
  - [Intent](#intent)
  - [Added functionality](#added-functionality)
  - [Database](#database)
  - [Non functional changes](#non-functional-changes)
  - [Ongoing development](#ongoing-development)
    - [Findings](#findings)

<!--TOC-->


## Note

These are short notes documenting functions added when porting to Python-3,
still to be considered experimental

## Intent

The idea was to make the package more usable in my own context, which concerns
Linux/Ubuntu or Docker produced logs. 

Other aspects:
 - emphasis on `fr_FR.UTF-8` locale
 - most logs are in `RSYSLOG_TraditionalFileFormat`
 - found `logjoin` interesting, but needed to change the DB interface:
   since I am running under `Mysql 8.0` which requires an up to date 
   version of the DB interface `SQLAlchemy`, I removed  `SQLSoup` 
   and converted to current version of`SQLAlchemy`, with interest on the ORM. This
   is used in `logjoin` and in the (added) `logdb`.
   
## Added functionality
 
1. added CLI flags to customize the level of logging; not customizable from 
   ~/.logtoolsrc (implementation propagates slowly to various entries)
    - adds flags `-s` (symbolic designation like ̀`-s DEBUG`)  `-n` (numerical
	 like `-n 10`). Symbolic names and values as in Python `logging` module.

    ```
    logparse --parser JSONParserPlus -f "{(Id|ContainerC.*)}" -s DEBUG 
    logparse --parser JSONParserPlus -f "{(Id|ContainerC.*)}" -s ERROR 
    ```

1. "INI" configuration files :
   CLI commands will look at the environment variable LOGTOOLS_RC, which should 
   contain a comma separated list of configuration files in INI format; if not set, 
   defaut "/etc/logtools.cfg:~/.logtoolsrc" is used. 
   ConfigParser is used in ExtendedInterpolation mode.
	 
1. Added RFC 5424 parser `SyslogRFC5424`, here ̀-f`supports symbolic field selection.
   This addition makes use of package `syslog_rfc5424_parser` from 
   https://github.com/EasyPost/syslog-rfc5424-parser. 

         ```
		 cat testData/testRFC5424.data | logparse --parser SyslogRFC5424 -f hostname -s INFO
         ```
		 
		 Field names can be found running with flag `-s DEBUG`	 

1. Added a facility to handle logs specified by "traditional templates" in the style
   defined at url   https://rsyslog-5-8-6-doc.neocities.org/rsyslog_conf_templates.html
   - <B>This is not compliant to said specification/standard</B>, only in <I>same style</I>
   - This is implemented (mostly) in `logtools/parsers2.py`
   - Parametrized by a textual description of templates in `logtools.parsers2.templateDef`
     where templates are defined in the style of traditional templates. 
	 + This can be extended by adding more templates. (However not all features are 
	   suppported)
     + When extending, you may either:
	   1. add special function definition
	      in  `logtools/parsers2.py`like :
	      ```
	      def FileFormat():
              return RSysTradiVariant("FileFormat")
	      ```
	      and add some import instructions in `logtools/_parse.py`.
	   2. use configuration definable field descriptions as explained below.

     + these formats forms a set extensible via configuration file(s):
       requires adding to `~/.logtoolsrc`
       ~~~
       RSysTradiVariant]
       HOME: <your home dir>
       file: ${HOME}/.logtools.d/<your extension file>
       ~~~
	   
	   and in the extension file:
	   
       ~~~
	   #$template TestA,"%HOSTNAME%"
       #$template TFFA,"%TIMESTAMP% %HOSTNAME%\n"
       #$template TFFB,"%TIMESTAMP% %HOSTNAME% %syslogtag%"
       #$template TFFC1,"%TIMESTAMP%"
       ~~~

	   
     + Fields can be selected by field number or by using the property (symbol) appearing 
	   in the template (for now, look for `templateDefs`  in `logtools/parsers2.py`).
	   
   - Usable with /var/log/{syslog,kern.log,auth.log} (on the Ubuntu Linux configuration
     described) and ̀docker container logs` (one of my use cases)
	 
   Examples of use:
    ```
	  cat /var/log/syslog | logparse --parser TraditionalFileFormat -f 3 -s ERROR 
  	  cat /var/log/syslog | logparse --parser TraditionalFileFormat -f msg -s ERROR 
      cat /var/log/syslog | logparse --parser TraditionalFileFormat -f TIMESTAMP \
	                                      -s ERROR
      cat testData/testCommonLogFmt.data | logparse --parser CommonLogFormat  \
	                                      -s INFO -f4								
    ```

1. Parsing of JSON Data

   supported in `logjoin` via frontend interface

1. Changes in `logjoin`. 

   + Data Base interface
     + removed all `SQLSoup` dependencies; moving to `SQLAlchemy`. This option
	   was selected because `SQLSoup` was found incompatible with newer versions 
       of  `SQLAlchemy`, making `Mysql 8.0` unavailable.
     + supports `Mysql 8.0` and `SQLite`
     + tested with both `Mysql 8.0` and ̀`SQLite`
	 
   + added `frontend` filtering
     + frontend may return JSON, internally as (recursive dict of list)...
	 + permits to ingest JSON data (see tests)
	 
   + added a (parameterizable) notion of `backend`
     + performs database operations depending of flow of data streaming out of `frontend`
	 + collect SQL Schema (tables) information from SQL server after connection,
	  this may be used to simplify emitting more sophisticated queries
     + generates SELECT SQL (for parameters in CLI or `~/.logtoolsrc`) using 
	  SQLAlchemy using either ORM or Core. 
	  
   + support of additional data base transactions:
     + table creation (for now table wired in, ... this may become parametrizable)
	 + able to use SQLAlchemy via non ORM connections and ORM sessions
	 + able to use "mapped table"
	

1. Changes in backend filtering

   + started with difficulties when piping into applications expecting ready to parse
     JSON structures as lines
   + distinguish form of returned data (string, binary, with filtering)
    - not systematic yet
  	
1. Changes  to ̀flattenjson`:

   + added --raw to dispense with utf-8 encoding, therefore can pipe to xargs,
	   did not change default for backwards compatibility. This could have a CLI 
	   like `--output-encoding`in `logjoin`

1. Addition of `logdb`

   This focuses on the performance of ORM supported database operations,
   the first example performing additions and updates based on the incoming flow
   of data from the logs.
   +  This uses quite general SQLAlchemy ORM tools, using Classes `SQLAlchemyDbOperator` 
     and `SQLAlchemyORMBackBase`, for providing 
     DB related operations, implemented in CLI program `logdb`, like:
    - filling a database table from data collected from a log stream
   + this is implemented with some generality in classes  `SQLAlchemyORMBackBase` 
     and `SQLAlchemyDbOperator` 
   + this feature is parametrized by CLI or config file; for now a single
     case has been implemented:
	
   +  `NestedTreeDbOperator ` (parm. `dbOperator: SQLAlcDbOp`
	  in `~/.logtoolsrc`) which provides for entering in a tree-like database schema the 
      content of  JSON (here from a Docker `inspect`   command):
   ~~~   
   {'TOP': [ {'IPAM': 
               {'Driver': 'default', 
                'Options': {}, 
				'Config': [ { 'Subnet': '172.19.0.0/16', 
				              'Gateway': '172.19.0.1'}]}, 
		      'Containers': {'4cf07fa937da4b6ad844b3a6ca22a8eb167dc503544becda8789774a6e605c5b': 
			                   {'Name': 'mysql1', 
							   'EndpointID': '7edb7b1e866957f0de6150c73c78b70717a6bb833794009509f1002dec622f41', 
							   'MacAddress': '02:42:ac:13:00:02', 
							   'IPv4Address': '172.19.0.2/16', 
							   'IPv6Address': ''}, 
						      '517acb5295aba5cc347d7aae88b525abf7faef26f5c481f2b82636b0619a192b': 
							   {'Name': 'mysql-workbench', 
							    'EndpointID': '5255215cc33826d3b90973aaed786d3b3e2b620ddbe6a837c6ae060fc8ce61e4', 
								'MacAddress': '02:42:ac:13:00:03', 
								'IPv4Address': '172.19.0.3/16', 
								'IPv6Address': ''}}}]}
   ~~~
   
      results in inserting the following data in the database:
   
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


  Still **in progress**:
  + in above example, the selection mechanism has removed 'IPAM' 
    and 'Containers'  keys.... which is obviously not a terrific idea!!
  + structurally, all methods dependent on the DB schema should be moved to
    file ̀ext_db.py`. 

## Database

   The ̀`logjoin` and `logdb` programs and the corresponding modules make 
   use of a database. Since the interface is done through SQLAlchemy,
   selection of the database interface is done in the ̀`connect_string`
   specified either by means of the INI configuration file or command
   line argument (or class constructor).
   
   The interface (and therefore the programs) is (are) (apparently)  mostly 
   independent of the database. However:
   1. we found that SQLite was not able to use `enum` type data, 
      which was OK for Mysql. 
   1. We provide ̀class `SQLite_Data_Standardize` (and base class 
      DB_Data_Standardize ) in `db_ext.py` to adjust
      for not supported data types. **If more numerous interfaces 
	  need data adaptation, the selection mechanism will need to be 
	  generalized in class  `NestedTreeDbOperator` CTOR.**

   Exemples are included in Github Actions CI tests, in ̀̀
   `.github/workflows/`.
   
## Non functional changes

1. removed most of the `eval` function calls by function `utils.getObj`,
   mostly to avoid code injection and hard to understand error messages.

## Ongoing development

The issues here should be resolved before this file hits Github!

 
Improvements TBD(?):
  1. change --raw in flattenjson to use  `--output-encoding`like `logjoin`
  1. document aux/parseRsyslogd.py, which is a **test tool** for users that
  add parsing variants via the `RSysTradiVariant` key in `.logtoolsrc`
	 
  
### Findings 
  1. flattenjson has (very) limited functionality...
    + added --raw to dispense with utf-8 encoding, therefore can pipe to xargs,
	  did not change default for backwards compatibility.

  1. Questions about transitionning in SQLAlchemy, found
     https://docs.sqlalchemy.org/en/14/tutorial/index.html, have been resolved
	 by keeping some Core based classes and moving to ORM for `_db.py` and CLI 
	 `logdb`
  


