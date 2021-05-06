# Collecting information via *logs*

## Goals

This file documents information which is available via logs or log
analysis on my Ubuntu Linux machine. Depending on my paranoia, I
may attempt to use this information or not

## TOC
<!--TOC-->

- [Collecting information via *logs*](#collecting-information-via-logs)
  - [Goals](#goals)
  - [TOC](#toc)
  - [Available logs on (default) Ubuntu installation](#available-logs-on-default-ubuntu-installation)
  - [Logs from Docker or containers](#logs-from-docker-or-containers)

<!--TOC-->


## Available logs on (default) Ubuntu installation

First, lets look at `/var/log`:
  1. alternatives.log      
	On Ubuntu, update-alternatives maintains symbolic links 
	determining default commands.
	
  1. apport.log  
  (!) Apport intercepts crashes right when they happen the first time,
  gathers potentially useful information about the crash and the OS environment.
  See https://wiki.ubuntu.com/Apport.
  
  1. apt/ directory
  Information about loaded packages
  
  1. auth.log  
  (!) Much authorization information
  
  1. boot.log 
  Binary, 
    + formatted by `journalctl -b`, 
	+ list of boots formatted by `journalctl --list-boots`
    + is this exploited by ̀last`
  
  1. bootstrap.log  
  
  1. `btmp` records failed login attempts
    + for now seems empty on my machine,...
    + formatted by `last`, bad attempts shown by `lastb`
	
  1. cups: 
    + why is this logging on my machine with no printer in sight?
	
  1. dist-upgrade : 
    + information about system upgrades
	
  1. dmesg
    + The dmesg command shows the current content of the kernel syslog 
	  ring buffer messages while the /var/log/dmesg file contains what 
	  was in that ring buffer when the boot process last completed.
    + the command requires root privilege, whereas the file is readable,
	  + need to understand how times are shown
	
  1. exim4
    + this is supposed to be an internet mailer...  
	+ see why is this installed?
	
	
  1. dpkg.log  
  
  1. faillog
     + there is a command to visualize, but results are strange!
  
  1. fontconfig.log  
  
  1. gpu-manager.log  
  
  1. installer
     + syslog related to `grub` installation (check)
      +partman: partitions (seems never purged..)
	 
  1. journal (related to `systemd`)
     + size can be controlled with journalctl, also
	   options in ̀/etc/systemd/journald.conf`
	 
  1. kern.log  
     + very detailed, lots for every restart from freeze
	 + may contain interesting security related/device related (showing a Yubikey and a flash-disk)
        ~~~
        usb 2-1: new full-speed USB device number 12 using xhci_hcd
        usb 2-1: New USB device found, idVendor=1050, idProduct=0116, bcdDevice= 3.50
        usb 2-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
        usb 2-1: Product: Yubikey NEO OTP+U2F+CCID
        usb 2-1: Manufacturer: Yubico
        input: Yubico Yubikey NEO OTP+U2F+CCID as /devices/pci0000:00/0000:00:14.0/usb2/2-1/2-1:1.0/0003:1050:0116.0006/input/input21
        hid-generic 0003:1050:0116.0006: input,hidraw1: USB HID v1.10 Keyboard [Yubico Yubikey NEO OTP+U2F+CCID] on usb-0000:00:14.0-1/input0
        hid-generic 0003:1050:0116.0007: hiddev1,hidraw2: USB HID v1.10 Device [Yubico Yubikey NEO OTP+U2F+CCID] on usb-0000:00:14.0-1/input1
        usb 2-1: USB disconnect, device number 12
        ~~~


        ~~~
        usb 2-1: new high-speed USB device number 13 using xhci_hcd
        usb 2-1: New USB device found, idVendor=090c, idProduct=1000, bcdDevice=11.00
        usb 2-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
        usb 2-1: Product: Flash Disk
        usb 2-1: Manufacturer: USB
        usb-storage 2-1:1.0: USB Mass Storage device detected
        usb-storage 2-1:1.0: Quirks match for vid 090c pid 1000: 400
        scsi host3: usb-storage 2-1:1.0
        usbcore: registered new interface driver usb-storage
        usbcore: registered new interface driver uas
        scsi 3:0:0:0: Direct-Access     USB      Flash Disk       1100 PQ: 0 ANSI: 4
        sd 3:0:0:0: Attached scsi generic sg1 type 0
        sd 3:0:0:0: [sdb] 31129600 512-byte logical blocks: (15.9 GB/14.8 GiB)
        sd 3:0:0:0: [sdb] Write Protect is off
        sd 3:0:0:0: [sdb] Mode Sense: 43 00 00 00
        sd 3:0:0:0: [sdb] Write cache: enabled, read cache: enabled, doesn't support DPO or FUA
        sdb: sdb1
        sd 3:0:0:0: [sdb] Attached SCSI removable disk
        FAT-fs (sdb1): Volume was not properly unmounted. Some data may be corrupt. Please run fsck.
        audit: type=1400 audit(1618061510.867:91): apparmor="DENIED" operation="open" profile="snap.gnome-system-monitor.gnome-system-monitor" name="/run/mount/utab" pid=4692 comm="gnome-system-mo" requested_mask="r" denied_mask="r" fsuid=1000 ouid=0
        audit: type=1400 audit(1618061528.811:92): apparmor="DENIED" operation="open" profile="snap.gnome-system-monitor.gnome-system-monitor" name="/run/mount/utab" pid=4692 comm="gnome-system-mo" requested_mask="r" denied_mask="r" fsuid=1000 ouid=0
        sdb: detected capacity change from 15938355200 to 0
        usb 2-1: USB disconnect, device number 13
        ~~~


  1. lightdm  : display manager, related to Xorg.\<dd\>.log where dd is the XWindows display 
     number
	 
  1. mysql : I have an unhappy mysql running somewhere... (Check)
  
  1. ntpd  : 
     + nothing in the logs, what is the status? 
	 + There is a ̀ntpq` program for querying the state
  
  1. pm-powersave.log  
     + powersave information

  1. pm-suspend.log  
     + hibernate information (does not seem much used recently (?))
  
  1. repowerd.log  
  
  1. sssd
     + SSSD provides a set of daemons to manage access to remote directories and authentication
       mechanisms. It provides an NSS and PAM interface toward the system and a pluggable backend
       system to connect to multiple different account sources as well as D-Bus interface. It is
       also the basis to provide client auditing and policy services for projects like FreeIPA.
       It provides a more robust database to store local users as well as extended user data.
  
     + does not seem to work:
        ~~~
	    (2021-04-08 23:29:46:488889): [sssd] [get_monitor_config] (0x0010): No domains configured.
        (2021-04-08 23:29:46:488915): [sssd] [main] (0x0020): SSSD couldn't load the configuration database.
        ~~~
  
  1. syslog
     + much to see (!!!)
 
  1. ubuntu-advantage.log  
  
  1. unattended-upgrades
     + not much information, except when these occur
  
  1. Xorg.0.log : see above

## Logs from Docker or containers
