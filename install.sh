#!/bin/bash
LOGFILE="install.log"

cp src/main.py /etc/init.d/weathermap.py
mkdir /var/local/weathermap > LOGFILE 2>>&1
mkdir /var/local/weathermap/cache
mkdir /var/local/weathermap/cache/nowcast
mkdir /var/local/weathermap/fonts
mkdir /var/local/weathermap/www

cp fonts/4x6.bdf /var/local/weathermap/fonts
cp -r www /var/local/weathermap/www

chgrp -R daemon /var/local/weathermap
chmod -R 775 /var/local/weathermap