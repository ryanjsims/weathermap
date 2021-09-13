#!/bin/bash
LOGFILE="install.log"
export FLASK_APP=weatherportal
CONFIG="/var/local/weathermap/instance/config.py"

echo "Creating directory structure"
cp init.d.sh /etc/init.d/weathermap > $LOGFILE 2>&1
mkdir /var/local/weathermap >> $LOGFILE 2>&1
mkdir /var/local/weathermap/cache >> $LOGFILE 2>&1
mkdir /var/local/weathermap/cache/nowcast >> $LOGFILE 2>&1
mkdir /var/local/weathermap/fonts >> $LOGFILE 2>&1

echo "Copying files..."
cp fonts/4x6.bdf /var/local/weathermap/fonts >> $LOGFILE 2>&1
cp main.py /var/local/weathermap/weathermap.py >> $LOGFILE 2>&1
cp -r weatherportal /var/local/weathermap/ >> $LOGFILE 2>&1

echo "Initializing instance files"
cd /var/local/weathermap
flask init-db
echo "import os" > $CONFIG
echo "dir_path = os.path.dirname(os.path.realpath(__file__))" >> $CONFIG
echo "" >> $CONFIG
SECRET=$(tr -dc A-Za-z0-9\!\#$\&\(\)\"\*+,-./\:\\\\\;\<=\>\?@[]^_\`{\|}~ </dev/urandom | head -c 25)
echo "SECRET_KEY = '$SECRET'" >> $CONFIG
SECRET=""
echo "DATABASE = os.path.join(dir_path, 'weatherportal.sqlite')" >> $CONFIG
cd -

echo "Setting permissions"
chgrp -R daemon /var/local/weathermap >> $LOGFILE 2>&1
chmod -R 775 /var/local/weathermap >> $LOGFILE 2>&1
chmod +x /etc/init.d/weathermap >> $LOGFILE 2>&1
chmod 660 $CONFIG

echo "Updating init.d"
update-rc.d weathermap defaults >> $LOGFILE 2>&1
echo -n "Done." >> $LOGFILE 2>&1

chown pi:pi $LOGFILE