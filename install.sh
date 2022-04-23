#!/bin/bash

function bye {
    echo "$1" >&2
    exit 1
}

[ "`id -u`" -eq 0 ] || bye "Aborted: this action requires root (sudo) access"

#copy configuration files
cp ./ioclogserver.service /etc/systemd/system || bye "Failed to copy ioclogserver.service"
cp ./ioclogserver.conf /etc || bye "Failed to copy ioclogserver.conf"

#create the log directory
LOGDIR=/var/log/epics
[ -d $LOGDIR ] || install -d -m755 "$LOGDIR" || bye "Failed to create $LOGDIR"

#copy source codes to $INSTALLDIR
INSTALLDIR=/usr/local/ioclogserv2
[ -d $INSTALLDIR ] || install -d -m755 "$INSTALLDIR" || bye "Failed to create $INSTALLDIR"
cp -fR twisted $INSTALLDIR
cp -fR ioclogserv $INSTALLDIR
[ $? -ne 0 ] && die "Failed to copy files to $INSTALLDIR" 

echo "Installation is done. Type 'systemctl start ioclogserver' to start the IOC log daemon"


