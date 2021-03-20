
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
		 cat testData/testRFC5424.data | logparse --parser SyslogRFC5424 -f hostname -s INFO
         ```
		 
		 Field names can be found running with flag `-s DEBUG`	 

3. Added a facility to handle logs specified by "traditional templates" in the style
   defined at url   https://rsyslog-5-8-6-doc.neocities.org/rsyslog_conf_templates.html
   - <B>This is not compliant to said specification/standard</B>, only in <I>same style</I>
   - This is implemented (mostly) in `logtools/parsers2.py`
   - Parametrized by a textual description of templates in `logtools.parsers2.templateDef`
     where templates are defined in the style of traditional templates. 
	 + This can be extended by adding more templates. (However not all features are 
	   suppported)
     + When extending, you must (in current state) add special function definition
	   in  `logtools/parsers2.py`like :
	   ```
	    def FileFormat():
            return RSysTradiVariant("FileFormat")
	   ```
	   and add some import instructions in `logtools/_parse.py`.
     + Fields can be selected by field number or by using the property (symbol) appearing 
	   in the template (for now, look for `templateDefs`  in `logtools/parsers2.py`).

   - Usable with /var/log/{syslog,kern.log,auth.log} (on the Ubuntu Linux configuration
     described)
	 
   Examples of use:
    ```
	  cat /var/log/syslog | logparse --parser TraditionalFileFormat -f 3 -s ERROR 
  	  cat /var/log/syslog | logparse --parser TraditionalFileFormat -f msg -s ERROR 
      cat /var/log/syslog | logparse --parser TraditionalFileFormat -f TIMESTAMP \
	                                      -s ERROR
      cat testData/testCommonLogFmt.data | logparse --parser CommonLogFormat  \
	                                      -s INFO -f4								
    ```
