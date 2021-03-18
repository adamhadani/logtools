# More documentation extracted from source

Included here is additional information extracted by reading the code.


## Per File / Script

### `logtools/parsers.py`


#### Formats supported

1. Apache access_log logfile parser.  See
    http://httpd.apache.org/docs/1.3/logs.html#accesslog"
  -  supported by `class AccessLog`
  -  includes the <B>Common Log Format</B>
  -  example: `127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /a.gif HTTP/1.0" 200 2326`

2. JSON log format
 - supported by `class JSONParser`
 
3.  uWSGI log format
 - uWSGI is a software application that "<I>aims at developing a full stack for 
   building hosting services</I>".
   -   https://en.wikipedia.org/wiki/UWSGI
 - the log format is described at https://uwsgi-docs.readthedocs.io/en/latest/LogFormat.html
 - supported by  `class uWSGIParser`


Examples of log formats are found in the test directory:

- Common Log Format :
	
	  ̀̀̀
       127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
       127.0.0.2 - jay [10/Oct/2000:13:56:12 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
      ̀̀̀
	  
- uWSGI : 

	  ̀̀̀
      [pid: 11216|app: 0|req: 2680/5864] 24.218.159.119 () {40 vars in 957 bytes} 
	    [Thu Jun 13 22:29:59 2013] 
		"GET /my/uri/path/?param_id=52&token=s61048gkje_l001z 
		   => generated 1813 bytes in 11 msecs (HTTP/1.1 200) 
		      2 headers in 73 bytes (1 switches on core 0)"
			  
      [pid: 11217|app: 0|req: 3064/5865] 10.18.50.145 () {34 vars in 382 bytes} 
	    [Thu Jun 13 22:30:00 2013] 
		"GET / => generated 8264 bytes in 9 msecs (HTTP/1.1 200) 
		      2 headers in 73 bytes (1 switches on core 0)"
	  ̀̀̀




### `logtools/_filter.py`
Provides `logfilter` script/command.  
 - Filter rows based on blacklists and field matching.
 - Several parser possibilities 


### `logtools/_filterbots.py`
Provides `filterbots` script/command.  
 - Filter rows based on regular expressions and  blacklists; match IP and User-Agent fields.
   - `--reverse` permits reverse filtering (show the excluded stuff)
 - Several parser possibilities 
   - flag : `--parser`,
        + Feed logs through a parser. Useful when reading encoded/escaped formats 
		  (e.g JSON) and when selecting parsed fields rather than matching via 
		  regular expression.
		  - value is name of parser class, to be `eval`'d (by Python's `eval` function),
		    and then instantiated
		  - available parsers are classes in `logtools/parsers.py`, which include:
		    + JSONParser,  
			+ AccessLog (Apache access_log logfile parser, which can
                                    consume arbitrary Apache log field directives, see 
									http://httpd.apache.org/docs/1.3/logs.html#accesslog ),
            + CommonLogFormat (derived from AccessLog ), specialized to
              parse the CLF Format, defined as:
               `%h %l %u %t \"%r\" %>s %b`
			   (see http://httpd.apache.org/docs/1.3/logs.html#accesslog)
			   
		    + uWSGIParser

          - <B>bottomline</B> : the parser returns a dict, out of which the fields 'ua' and
		    'ip' are extracted (modulo redefinition by flag `-f`) and filtered through 
			blacklist. 
			 + Any error, including
			'  KeyError' cause emission via log of ERROR message `No match for line`
			 + Lines are filtered out for corresponding to <I>Bots</I>
			 + other lines are transmitted
			
        + requirements : 
          - flags `-f` or `--ip-ua-fields` define field(s) selector for filtering bots 
		   when using a parser . Value format should be 
		   `'ua:<ua_field_name>,ip:<ip_field_name>'`. 
           If one of these is  missing, it will not be used for filtering.
   
    - default : the default is .... A regular expression can be specified using `-r` flag
	      to match IP/useragent fields; groups  'ip' and 'ua' receive special processing 
		  quite similar to what is described above at  '<B>bottomline</B>': 
		  + `ìp`: check whether ip in IP blacklist
		  + `ua`: 
   
   
### `logtools._flattenjson`

Extracts objects (dictionaries) from inside a JSON list;
 - Useful when piping into tools such as `json2csv` which expect "flat" json streams.

### `logtools._join`

Perform a join between log stream and some other arbitrary source of data.
 - Can be used with pluggable drivers e.g to join against database, other files etc.


### `logtools._merge`

Logfile merging utilities.
 - These typically help in streaming multiple individually sorted input logfiles 
   through, outputting them in combined sorted order (typically by date field)
   
   
###  `logtools._plot`
Plotting methods for logfiles

### `logtools._qps`
Compute QPS (Query Per Second) estimates based on parsing of timestamps from logs on
sliding time windows.

### `logtools._sample`
Sampling tools for logfiles

### `logtools._serve`

Miniature web server for delivering real-time OLAP-style log stats.


### `logtools._sumstat`

Generates summary statistics for a given logfile of the form:
`<count> <value>`

 - logfile is expected to be pre-sorted by count.

### `logtools._tail`

A tail-like utility that allows tailing via time-frames and more complex
expressions.


### `logtools._urlparse`

Parses URLs, Decodes query parameters,and allows some selection on URL parts.

