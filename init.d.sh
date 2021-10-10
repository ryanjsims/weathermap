#!/bin/bash
# /etc/init.d/weathermap
### BEGIN INIT INFO
# Provides:          weathermap
# Required-Start:    $dhcpcd $network $remote_fs $syslog
# Required-Stop:     $dhcpcd $network $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Display weathermap on boot
# Description:       Displays a weathermap on the connected led grid
### END INIT INFO
cd /var/local/weathermap
if [ "$1" == "start" ]; then 
    /usr/bin/python3 weathermap.py &
    echo $! > pid_file
elif [ "$1" == "stop" ]; then
    xargs -a pid_file kill
    rm pid_file
    /usr/bin/python3 clear.py
fi