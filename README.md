IOC log daemon v2
=================

This daemon is a drop in replacement for iocLogServer
which ships with EPICS Base.
It incorporates a number of differences (hopefully improvements).

1. Log file rotation instead of overwriting
1. Log IPs instead of host name (faster and doesn't truncate)
1. Supports filtering of caputlog entries base on user name
1. Supports re-broadcast of log messages over TCP

Dependencies
------------

Requires: python-twisted-core >= 10.0
Tested on: py2.7/Twisted-20.3.0 (pip2 install twisted), py3.6/Twisted-19.10.0

Configuration
-------------

The provided [ioglogserver.conf](ioclogserver.conf) should work for most sites.
It listens on the default port 7004, writes all entries to epics.log,
and re-broadcasts on port 7014.

Also provided is [ioglogserver_bnl.conf](ioclogserver_bnl.conf) which demonstrates
filtering caputlog entries by user name.
