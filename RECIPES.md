# logtools RECIPES

## TOC
<!--TOC-->

- [logtools RECIPES](#logtools-recipes)
  - [TOC](#toc)

<!--TOC-->


1. The following example demonstrates specifying a custom regular expression for matching
	the ip/user agent using the filterbots tool.
	Notice the use of named match groups syntax in the regular expression - (?P<name>...).
	The ips/useragents files are not specified in commandline and therefore are assumed to be defined
	in ~/.logtoolsrc or /etc/logtools.cfg as described above. For an example bots black list file, see the included data/examples directory.
	The option --print is used to actually print matching lines, rather than just report the filtering statistics.

	```
	cat error_log.1 | filterbots -r ".*\[client (?P<ip>.*?)\].*USER_AGENT:(?P<ua>.*?)\'" --print
	```

	Notice that its easy to reverse the filtermask simply by adding the --reverse flag. This is useful e.g
	to inspect all the filtered (bot) lines.

	```
	cat error_log.1 | filterbots -r ".*\[client (?P<ip>.*?)\].*USER_AGENT:(?P<ua>.*?)\'" --print --reverse
	```

1. filterbots can also route input to a custom parser (see logtools.parsing module), for example:

	```
	cat request_log.json | filterbots --parser JSONParser -f 'ua:user_agent,ip:user_ip'
	```

	This will parse the JSON log, and use the fields called 'user_agent' and 'user_ip' for filtering bots.

1. The following example demonstrates using the geoip wrapper (Uses Maxmind GeoIP package). This will
	emit by default lines of the form '<ip>	<country>', per each input log line.

	```
	cat access_log.1 | geoip -r '.*client (.*?)\]'
	```

1. Merge (individually sorted) log files from multiple webapps and output combined and (lexically) sorted stream:

	```
	logmerge -d' ' -f1 app_log.1 app_log.2
	```

	Note that the -d (delimiter) and -f (field) are used to specify which field is used
	for the sort-merging (in this case, the first field should be used)

1. Merge and sort numerically on some numeric field:

	```
	logmerge -d' ' -f3 --numeric app_log.*
	```

1. Use a custom parser for sort/merge. In this example, parse CommonLogFormat and sort by date:

	```
	logmerge --parser CommonLogFormat -f4 access_log.*
	```

1. Use logparse to parse a CommonLogFormat log (e.g Apache access_log) and print only the date field:

	```
	cat access_log | logparse --parser CommonLogFormat -f4
	```

1. Use logparse to parse a custom format Apache access_log and print first two fields.

	```
	cat my_access_log | logparse --parser AccessLog --format '%h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"' -f1,2
	```

	You might recognize this format as the NCSA extended/combined format.

1. Use logparse to parse a JSON-format log (each line is a JSON string)
	and print only the client_ip, useragent fields:

	```
	cat json_access_log | logparse --parser JSONParser -f 'client_ip,useragent'
	```

1. Generate a pie chart of Country distributions in Apache access_log using
	Maxmind GeoIP and GoogleChart API.
	Note that this requires the GeoIP library and python bindings as well as pygooglechart package.

	```
	cat access_log.1 | geoip -r '^(.*?) -' | aggregate -d$'\t' -f2 | \
			logplot -d' ' -f1 --backend gchart --type pie -W600 -H300 --limit 10 --output plot.png
	```

1. Filter bots and aggregate IP address values to show IPs of visitors with counts and sorted from most frequent to least:

	```
	cat access_log.1 | filterbots --print | aggregate -d' ' -f1
	```

1. Create a running average of QPS for a tomcat installation, using time windows of 15 seconds:

	```
	cat catalina.out | qps -r'^(.*?) org' --dateformat '%b %d, %Y %I:%M:%S %p' -W15 --ignore
	```
	
1. Create a running average of QPS for a uWSGI webserver, ignoring lines with parse errors, using time window of 1 second. This handles time format that looks like 'Thu Jan 14 00:45:31 2016':

   ```
   cat uwsgi.log | qps -i -r '.*\} \[(.*)\] ' -F '%a %b %d %H:%M:%S %Y' -W 1
   ```
   
1. Parse URLs from log and print out a specific url query parameter:

	```
	cat access_log.1 | grep -o 'http://[^\s]+' | urlparse --part query -q 'rows'
	```

1. Create a join between some extracted log field and a DB table using logjoin:
	the logjoin utility is a very powerful tool that lets you create some joins on the fly.
	While its not ment for large scale joins (there is no batching at the moment), it can be
	very instrumental when trying to map information from logs to entries in a DB manually
	or on small increments:

	```
	cat my_log.json | logparse --parser JSONParser -f 'my_join_field' | logjoin
	```

1. Filter lines from log using the blacklist file-based logfilter tool. We use Aho-Corasick exact string matching
    as well as a custom parser to filter a JSON log format, while ignoring case:

    ```
    cat my_log.json | logfilter --parser JSONParser -f'user_query' --blacklist queries_blacklist.txt --with-acora --ignore-case --print
    ```

1. Compute percentiles from numerical data:

    ```
    cat my_response_times.log | percentiles
    ```

1. Tail a log, printing only lines which occured on or after 03/20/2013:

	```
	cat my_log.log | logtail --date-format '%Y-%m-%d' --start-date '03/20/2013' --print
	```

1. Extract a 'results' key from JSON stream and output its items individually per-line:

    ```
    cat my_json_blob.json | flattenjson -f 'results'
    ```

    NOTE: The output is not valid JSON, but rather valid JSON per-line. Useful for working with json2csv
    which acknowledges such a format and does not support easily nested json structures.

** Naturally, piping between utilities is useful, as shown in most of the examples above.

** All tools admit a --help command-line option that will print out detailed information about the different
   options available.
