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


### `logtools/_filter.py`
Provides `logfilter` script/command.  
 - Filter rows based on blacklists and field matching.
 - Several parser possibilities 


### `logtools/_filterbots.py`
Provides `filterbots` script/command.  
 - Filter rows based on blacklists; match IP and User-Agent fields.
 - Several parser possibilities 

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

