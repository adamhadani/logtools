# Python-3 port

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
  Current versions are
  `sqlsoup 0.9.1` and  `SQLAlchemy 1.4.0b3`. This port has been made requiring specific
  versions under `virtualenv`; `setup.py`has been changed accordingly. A file
  [requirements.txt](./requirements.txt) has been added to document this, and
  can be used with `pip3`.
  
- the package's usage of `datetime.strptime` in my locale `"fr_FR.UTF-8"`was found
  problematic ( `testQps` <I>fails when parsing date</I> `11/Oct/2000:14:01:14 -0700`
  <I>which is fine in my locale</I>) : 
  disabled statements `locale.setlocale(locale.LC_ALL, "")`in 
  `_qps.py` and `_plot.py`. 
  The directory `aux` has been added with script `testStrptime.py` to test 
  under different locales.
  
### Added functionality

1. added CLI flags to customize the level of logging; not customizable from 
   ~/.logtoolsrc (propagates slowly to various entries)

  
### Test and operative environment

 - a `virtualenv`environment has been set up, requiring Python 3.8.6, which happens
 to be the native Python-3 on my system: `virtualenv -p 3.8.6` 
 - it has been populated according to requirements
 - installation and use of the package are all performed under this environment
 
### Installation
 
 This may be done as follows:

 - setup the `virtualenv` environment
 - change directory to the package (where `setup.py` is found)
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
 
 - configuration: see `~/.logtoolsrc`
 
 - filterbots`: 
 
 ```
touch bots_hosts.txt         # File designated in ~/.logtoolsrc
touch bots_useragents.txt    # File designated in ~/.logtoolsrc
cat /var/log/auth.log | filterbots --print
 ```
 
 
