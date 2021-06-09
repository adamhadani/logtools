# logtools

## TOC
<!--TOC-->

- [logtools](#logtools)
  - [TOC](#toc)
  - [Derived Version Notice](#derived-version-notice)
  - [<CENTER>Original README</CENTER>](#original-readme)
    - [A log files analysis / filtering framework.](#a-log-files-analysis--filtering-framework)
  - [Installation](#installation)
    - [Python2](#python2)
    - [Python3](#python3)
  - [Console Scripts](#console-scripts)
  - [Configuration](#configuration)
  - [Usage Examples](#usage-examples)
  - [Credits](#credits)
  - [Contact](#contact)
  - [License](#license)

<!--TOC-->


## Derived Version Notice
   This is a derived version of <B>logtools</B>, 
   including a port to Python-3 and
   additional features. 
   - The original version, for Python-2 (<I>as far as I know</I>), by Adam Ever-Hadani  is available at
     http://github.com/adamhadani <IMG SRC="https://travis-ci.org/adamhadani/logtools.svg?branch=master"/>.
   - This version, for <B>Python-3 only</B>, with additions and changes by  Alain Lichnewsky,   is available at 
     https://github.com/AlainLich/logtools
     distributed <I>as is</I>, with no warranty, under the Apache 2.0 license. 
	 + For features see
	   [PYTHON3-README.md](./PYTHON3-README.md) 
	   and [PYTHON3-ADDITIONS.md](./PYTHON3-ADDITIONS.md).
	 
<B>Notes</B>: this version
   -  is not compatible with Python-2
   -  has been tested in the following configurations

      <TABLE>
      <TH>
	      <TD>Development</TD><TD>Github Actions</TD>
	  </TH>
      <TR>
	      <TD COLSPAN="3"><CENTER><B>Status</B></CENTER></TD>
	  </TR>
	  </TR>
	      <TR><TD>Status</TD><TD>OK on dev. machine</TD>
	      <TD> <IMG SRC="https://github.com/AlainLich/logtools/actions/workflows/pythonExercise.yml/badge.svg?branch=ALPython3"/></TD>
	  </TR>
	  </TR>
	      <TR><TD>Status Extensions Mysql</TD><TD>OK on dev. machine</TD>
	      <TD> <IMG SRC="https://github.com/AlainLich/logtools/actions/workflows/pythonDBExercise.yml/badge.svg?branch=ALPython3" /></TD>
	  </TR>
	  </TR>
	      <TR><TD>Status Extensions SQLite</TD><TD>OK on dev. machine</TD>
	      <TD> <IMG SRC="https://github.com/AlainLich/logtools/actions/workflows/pythonSQLiteExercise.yml/badge.svg?branch=ALPython3" /></TD>
	  </TR>
      <TR>
	      <TD COLSPAN="3"><CENTER><B>Test Configurations</B></CENTER></TD>
	  </TR>
      <TR>
	      <TD ROWSPAN="2">System</TD><TD>Ubuntu 20.10</TD><TD ROWSPAN="2">Ubuntu 20.04.2 LTS</TD>
	  </TR>
      <TR>
	      <TD>Ubuntu 21.04</TD>
	  </TR>
      <TR>
	      <TD>Linux</TD><TD>5.8.0-25-generic </TD><TD></TD>
	  </TR>
      <TR>
	      <TD ROWSPAN="2">Python</TD><TD>3.8.6</TD><TD ROWSPAN="2">CPython 3.8.10</TD>
	  </TR>
      <TR>
	      <TD>3.9.4</TD>
	  </TR>
      <TR>
	      <TD>virtualenv</TD><TD>20.0.29+d</TD><TD>not used</TD>
	  </TR>
      <TR>
	      <TD>Used modules</TD><TD>see <A HREF="./requirements.txt">requirements.txt</A> 
		  </TD>
		  <TD><A HREF="./requirements.txt">requirements.txt</A>, and 
              <A HREF="./aux/testData/ActionsMysqlTest/scripts/testsDB.requirements">for test</A>
          </TD>
	  </TR>
	  <TR>
	      <TD>Locale</TD><TD>fr_FR.UTF-8</TD><TD>C.UTF-8</TD>
	  </TR>
	  <TR>
	      <TD rowspan="3">Mysql</TD><TD>DockerHub reference</TD>
		  <TD><A HREF="https://github.com/actions/virtual-environments/blob/main/images/linux/Ubuntu2004-README.md">
		  Github VM standard
		  </A></TD>
	  </TR>
	  <TR>
	      <TD>mysql/mysql-server:latest</TD><TD>MySQL 8.0.25</TD>
	  </TR>
	  <TR>
	      <TD>2021-01-19T14:27:35</TD><TD></TD>
	  <TR>
	      <TD>SQLite</TD><TD>3.34.1</TD><TD></TD>
	  </TR>
      </TABLE>
   

----------------------------------------------------------

## <CENTER>Original README</CENTER>

----------------------------------------------------------


<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [logtools](#logtools)
    - [A log files analysis / filtering framework.](#a-log-files-analysis--filtering-framework)
  - [Installation](#installation)
  - [Console Scripts](#console-scripts)
  - [Configuration](#configuration)
  - [Usage Examples](#usage-examples)
  - [Credits](#credits)
  - [Contact](#contact)
  - [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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
### Python2
<B>Note</B> <I>This applies to the original package, not the port in this directory; please 
see [Adam Ever-Hadani](http://github.com/adamhadani/) site and original version.</I>

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
	
### Python3

Concerning the Python3 port, see  [PYTHON3-README.md](./PYTHON3-README.md)

For installation, see  [PYTHON3-README.md](./PYTHON3-README.md#installation), 
much information can be
gleaned from [Github Actions YAML](.github/workflows/pythonExercise.yml). 

## Console Scripts

* ``filterbots``
	Used to filter bots based on an ip blacklist and/or a useragent blacklist file(s).
    The actual regular expression mask used for matching is also user-specified,
    so this can be used with any arbitrary log format (See examples below).
	Blacklist files can specify both exact match as well as more complex matching
	types (prefix/suffix match, regexp match. See examples below).

* ``geoip`` (Not ported to Python-3)
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

* ``logtail``
	Tail a logfile, based on more complex expressions rather than the number of lines N to limit to. Currently supported is
    tailing via a date format/expression, e.g filter only to lines in which the date expression is equal or greater than
    a given start date.

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

* ``flattenjson``
    Extract a key from a JSON blob pointing to a list of items (e.g dictionaries) and output the dictionaries
    as individual JSON lines. Useful for bridging into tools such as json2csv

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

See [RECIPES](./RECIPES.md)

## Credits

logtools was created by [Adam Ever-Hadani](http://github.com/adamhadani/)

## Contact

Adam Ever-Hadani

- http://github.com/adamhadani
- http://www.linkedin.com/in/adamhadani
- adamhadani@gmail.com

## License

logtools is available under the Apache license 2.0. See the LICENSE file for more info.

