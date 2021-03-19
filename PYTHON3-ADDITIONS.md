
# Additional features in Python-3 port

## Note

These are short notes documenting functions added when porting to Python-3,
still to be considered experimental

## Intent

The idea was to make the package more usable in my own context, which concerns
Linux/Ubuntu produced logs. 

Other aspects:
 - emphasis on `fr_FR.UTF-8` locale
 - most logs are in `RSYSLOG_TraditionalFileFormat`
 
### Added functionality
 
1. added CLI flags to customize the level of logging; not customizable from 
   ~/.logtoolsrc (propagates slowly to various entries)
    - adds flags `-s` (symbolic designation like ̀-s DEBUG`)  `-n` (numerical
	 like `-n 10`)
	 
	 
2. Added RFC 5424 parser `SyslogRFC5424`, here ̀-f`supports symbolic field selection.
   This addition makes use of package `syslog_rfc5424_parser` from 
   https://github.com/EasyPost/syslog-rfc5424-parser. 

         ```
         cat testData/tytyRFC.log | testLogparse --parser SyslogRFC5424 -f hostname -s INFO
         ```
		 
		 Field names can be found running with flag `-s DEBUG`	 

3. Looking at parser for `RSYSLOG_TraditionalFileFormat`
        Keep you posted!
