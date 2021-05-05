# Cheatsheet on format selection

## TOC
<!--TOC-->

- [Cheatsheet on format selection](#cheatsheet-on-format-selection)
  - [TOC](#toc)
  - [Goal and summary](#goal-and-summary)
  - [Date](#date)

<!--TOC-->

## Goal and summary

According to the look of a log, which format to look for first!

  - <I>Devised as a self-help, will expand this to cover tests 
       and use cases</I>
  
## Date

<TABLE>
<TR>
    <TD rowspan=4>program default</TD> 
	<TD rowspan=4>-r</TD>
	<TD>/var/log/auth</TD>
	<TD>Mar 19 09:17:26</TD>
</TR>
<TR>
	<TD>/var/log/kern.log</TD>
	<TD rowspan=2>Sun Mar 21 12:59:57 2021</TD>
</TR>
<TR>
	<TD>/var/log/apport.log</TD>
</TR>
<TR>
	<TD>last</TD>
	<TD>Wed Dec 30 11:51</TD>
</TR>
<TR>
    <TD>Common Log Format</TD> 
	<TD>--parser CommonLogFormat</TD>
	<TD></TD>
	<TD>10/Oct/2000:13:55:36 -0700</TD>
</TR>
<TR>
    <TD rowspan=3>RFC5424</TD> 
	<TD rowspan=3 >--parser SyslogRFC5424</TD>
	<TD>Mysql</TD>
	<TD>2021-03-19T08:21:10.226123Z</TD>
</TR>
<TR>
	<TD></TD>
	<TD>2016-01-15T01:00:43Z</TD>
</TR>
<TR>
	<TD>Github</TD>
	<TD>2021-03-22T16:50:52.6302582Z</TD>
</TR>
<TR>
	<TD></TD>
    <TD></TD> 
	<TD></TD>
	<TD></TD>
</TR>
<TR>
	<TD></TD>
    <TD></TD> 
	<TD></TD>
	<TD></TD>
</TR>
</TABLE>

