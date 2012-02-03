# logtools

### A log files analysis / filtering framework.

logtools encompasses of a few easy-to-use, easy to configure command-line
tools, typically used in conjunction with Apache logs (but not only).

The idea is to standardize log parsing and filtering using a simple, coherent
configuration methodology and UNIX/POSIX-like command-line interface (STDIN input streaming, command piping etc.),
so as to create a consistent environment for creating reports, charts and other such
log mining artifacts that are typically employed in a Website context.

logtools can be used either programmatically from within a python program, or as a set of 
atomic command-line utilities. See below for description of the command-line tools. 

For help on using the programmatic interface, I'm working on creating API
documentation using Sphinx. For now, the source code itself is fairly well
commented.

This software is distributed under the Apache 2.0 license.


## Installation

To install this package and associated console scripts, unpack the distributable tar file,
or check out the project directory, and then run:

	python setup.py install

You will need sudo/root rights to install this in the global system python installation.
Alternatively, you can install logtools into a python virtualenv. See http://pypi.python.org/pypi/virtualenv

To run unit tests, issue this command:

	python setup.py test

You can also issue the following to get code-coverage report (needs the coverage python package):

	python setup.py nosetests

If for some reason setuptools does not install 'nose' by default, 
you can easily install it if you have setuptools installed by running:
	
	easy_install nose


## Console Scripts

* ``filterbots``
	Used to filter bots based on an ip blacklist and/or a useragent blacklist file(s).
    The actual regular expression mask used for matching is also user-specified,
    so this can be used with any arbitrary log format (See examples below).
	Blacklist files can specify both exact match as well as more complex matching 
	types (prefix/suffix match, regexp match. See examples below).

* ``geoip``
	Simple helper utility for using the Maxmind GeoIP library to tag log lines by the IP's country.
        The regular expression mask used for matching the IP in the log line is user-specified.
	This tool requires the Maxmind GeoIP library and python bindings. See http://www.maxmind.com/app/country
			
* ``logparse``
	Use the logtools.parsers module to intelligibly parse the log, emitting/filtering user-selectable field(s).
	This can be used for inspecting logs whos format is harder to parse than simply cut-ing on whitespace,
	e.g CLF, JSON and so forth.

* ``logmerge``
	Merge multiple (individually sorted) input logstreams and stream them out in (combined) sorted order.
	This is useful for combining logs from multiple traffic-serving machines (e.g in a load-balanced environment)
	into a single stream which is globally ordered.

* ``logjoin``
	Perform a join on some field between input log stream and an additional, arbitrary source of data.
	This uses a pluggable driver (similar to logparse) allowing all kinds of joins, e.g between logfile and
	a database, filesystem objects etc. See examples below.
	
* ``logsample``
	Produce a random sample of lines from an input log stream. This uses Reservoir Sampling to
    efficiently produce a random sampling over an arbitrary large input stream.
	Both uniformly random as well as weighted random variants are available. See examples below.

* ``logfilter``
	Parse a log file and perform generic blacklist/whitelist-based row filtering against a specific field in the log row. Can use
	simple delimited field formats, or use a parser (see logtools.parsers) for dealing with more complex formats/encodings, 
	e.g JSON
	
* ``qps``
	Compute QPS averages given a log file using a datetime/timestamp field and a sliding window interval 
    specified by the user. Can be very handy to quickly assess current QPS of some arbitrary service
	based on real-time logfiles (e.g Apache access_log, Tomcat catalina.out).
		
* ``aggregate``
	Convenient shortcut for aggregating values over a given field and sorting/counting by a value's frequency.
	See example below.

* ``logplot``
	Render a plot based on some fields/values from input log. This tool supports a pluggable backend interface,
	and currently includes an implementation for plotting using the Google Charts API as well as matplotlib.
	See examples below.

* ``urlparse``
	Parse URLs and extract specific fields from them (domain, path, query parameters), also decoding various
	URL encoding formats .

* ``sumstat``
	Display various summary statistics from a logfile/dataset given as a histogram (e.g (<count>,<value>) rows).
	This includes average, min/max, percentiles etc. 

* ``percentiles``
	A quick and simple utility to compute percentiles from input numeric values.

## Configuration

All tools' command-line parameters can assume a default value using parameter interpolation
from /etc/logtools.cfg and/or ~/.logtoolsrc, if these exist.
This allows for convenient operation in the usual case where these rarely change, or when they 
assume one of a small set of different configurations (e.g usage profiles).

The basic configuration file format is of the form:

```
 [script_name]
 optname: optval
```

For example:

```
 [geoip]
 ip_re: ^(.*?) -

 [filterbots]
 bots_ua: /home/www/conf/bots_useragents.txt
 bots_ips: /home/www/conf/bots_hosts.txt
 ip_ua_re: ^(?P<ip>.*?) -(?:.*?"){5}(?P<ua>.*?)"
```

Available parameters per each command-line tool can be gleaned by running the 
tool with the --help flag.

Different configuration 'profiles' can also be specified. This is useful for cases
where you have a set of common, distinct configurations that you'd like to keep around.
All the tools admit a -P/--profile <profile_name> flag that will try to load default parameter
values from a [<profile_name>] section in the aforementioned .ini files. e.g:

```
filterbots --profile fbots_accesslog
```

will look up default parameter values from the section [fbots_accesslogs] in ~/.logtoolsrc or /etc/logtools.cfg
if that exists.


## Usage Examples

1. The following example demonstrates specifying a custom regular expression for matching
	the ip/user agent using the filterbots tool. 
	Notice the use of named match groups syntax in the regular expression - (?P<name>...).
	The ips/useragents files are not specified in commandline and therefore are assumed to be defined
	in ~/.logtoolsrc or /etc/logtools.cfg. For example bots black list files, see data/examples directory.
	The option --print is used to actually print matching lines, rather than just report the filtering statistics.
	
	```
	cat error_log.1 | filterbots -r ".*\[client (?P<ip>.*?)\].*USER_AGENT:(?P<ua>.*?)\'" --print
	```
	
	Notice that its easy to reverse the filtermask simply by adding the --reverse flag. This is useful e.g
	to inspect all the filtered (bot) lines.
		
	```
	cat error_log.1 | filterbots -r ".*\[client (?P<ip>.*?)\].*USER_AGENT:(?P<ua>.*?)\'" --print --reverse
	```

2. filterbots can also route input to a custom parser (see logtools.parsing module), for example:

	```
	cat request_log.json | filterbots --parser JSONParser -f 'ua:user_agent,ip:user_ip'
	```
	
	This will parse the JSON log, and use the fields called 'user_agent' and 'user_ip' for filtering bots.
	   
3. The following example demonstrates using the geoip wrapper (Uses Maxmind GeoIP package). This will
	emit by default lines of the form '<ip>	<country>', per each input log line.
	
	```
	cat access_log.1 | geoip -r '.*client (.*?)\]'
	```

4. Merge (individually sorted) log files from multiple webapps and output combined and (lexically) sorted stream:

	```	
	logmerge -d' ' -f1 app_log.1 app_log.2
	```
	
	Note that the -d (delimiter) and -f (field) are used to specify which field is used
	for the sort-merging (in this case, the first field should be used)

5. Merge and sort numerically on some numeric field:

	```
	logmerge -d' ' -f3 --numeric app_log.*
	```
		
6. Use a custom parser for sort/merge. In this example, parse CommonLogFormat and sort by date:

	```
	logmerge --parser CommonLogFormat -f4 access_log.*
	```

7. Use logparse to parse a CommonLogFormat log (e.g Apache access_log) and print only the date field:

	```
	cat access_log | logparse --parser CommonLogFormat -f4
	```

8. Use logparse to parse a custom format Apache access_log and print first two fields.

	```
	cat my_access_log | logparse --parser AccessLog --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"' -f1,2
	```
	
	You might recognize this format as the NCSA extended/combined format.
		
9. Use logparse to parse a JSON-format log (each line is a JSON string) 
	and print only the client_ip, useragent fields:
	
	```
	cat json_access_log | logparse --parser JSONParser -f 'client_ip,useragent'
	```

10. Generate a pie chart of Country distributions in Apache access_log using 
	Maxmind GeoIP and GoogleChart API. 
	Note that this requires the GeoIP library and python bindings as well as pygooglechart package.
	
	```
	cat access_log.1 | geoip -r '^(.*?) -' | aggregate -d$'\t' -f2 | \
			logplot -d' ' -f1 --backend gchart --type pie -W600 -H300 --limit 10 --output plot.png
	```

11. Filter bots and aggregate IP address values to show IPs of visitors with counts and sorted from most frequent to least:

	```
	cat access_log.1 | filterbots --print | aggregate -d' ' -f1
	```

12. Create a running average of QPS for a tomcat installation, using time windows of 15 seconds:

	```
	cat catalina.out | qps -r'^(.*?) org' --dateformat '%b %d, %Y %I:%M:%S %p' -W15 --ignore
	```

13. Parse URLs from log and print out a specific url query parameter:

	```
	cat access_log.1 | grep -o 'http://[^\s]+' | urlparse --part query -q 'rows'
	```

14. Create a join between some extracted log field and a DB table using logjoin:
	the logjoin utility is a very powerful tool that lets you create some joins on the fly.
	While its not ment for large scale joins (there is no batching at the moment), it can be
	very instrumental when trying to map information from logs to entries in a DB manually
	or on small increments:
	
	```
	cat my_log.json | logparse --parser JSONParser -f 'my_join_field' | logjoin
	```

** Naturally, piping between utilities is useful, as shown in most of the examples above.
	
** All tools admit a --help command-line option that will print out detailed information about the different
   options available.

## Credits

logtools was created by [Adam Ever-Hadani](http://github.com/adamhadani/)

## Contact

Adam Ever-Hadani

- http://github.com/adamhadani
- http://www.linkedin.com/in/adamhadani
- adamhadani@gmail.com

## License

logtools is available under the Apache license 2.0. See the LICENSE file for more info.

