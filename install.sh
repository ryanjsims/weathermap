#!/bin/bash
LOGFILE="install.log"

cp init.d.sh /etc/init.d/weathermap > $LOGFILE 2>&1
mkdir /var/local/weathermap >> $LOGFILE 2>&1
mkdir /var/local/weathermap/cache >> $LOGFILE 2>&1
mkdir /var/local/weathermap/cache/nowcast >> $LOGFILE 2>&1
mkdir /var/local/weathermap/fonts >> $LOGFILE 2>&1

cp fonts/4x6.bdf /var/local/weathermap/fonts >> $LOGFILE 2>&1
cp main.py /var/local/weathermap/weathermap.py >> $LOGFILE 2>&1
cp -r weatherportal /var/local/weathermap/ >> $LOGFILE 2>&1

chgrp -R daemon /var/local/weathermap >> $LOGFILE 2>&1
chmod -R 775 /var/local/weathermap >> $LOGFILE 2>&1
chmod +x /etc/init.d/weathermap >> $LOGFILE 2>&1

update-rc.d weathermap defaults >> $LOGFILE 2>&1
echo -n "Done." >> $LOGFILE 2>&1

chown pi:pi $LOGFILE