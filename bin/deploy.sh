#!/bin/bash

# COLORS
# Reset
Color_Off=$'\e[0m' # Text Reset

# Regular Colors
Red=$'\e[0;31m'    # Red
Green=$'\e[0;32m'  # Green
Yellow=$'\e[0;33m' # Yellow
Purple=$'\e[0;35m' # Purple
Cyan=$'\e[0;36m'   # Cyan


# Check if root
if [[ $EUID -ne 0 ]]; then
    echo -n "$Red"
    echo "You need to be root to perform this command"
    echo "Restart the script as super user or using 'sudo'$Color_Off"
    exit 1
fi

# Checking if python >= 3.7 is installed
if ! hash python3; then
    echo "Python3:$Red ERROR - Python 3.7 (or a more recent version) must be installed (see: https://www.python.org/).$Color_Off" >&2
    exit 1
fi
ver=$(python3 --version 2>&1 | sed 's/.* \([0-9]\).\([0-9]\).*/\1\2/')
if [[ "$ver" -lt "37" ]]; then
    echo "python3:$Red ERROR - $(python3 -V | tr -d '\n') found, should be at least 3.7 (see: https://www.python.org/).$Color_Off" >&2
    exit 1
fi
echo "python3:$Green OK !$Color_Off"

# Check if apache2 is installed
if dpkg -l apache2 &>/dev/null; then
    echo "apache2:$Green OK !$Color_Off"
else
    echo "apache2:$Red ERROR - Apache 2 must be installed (see: http://httpd.apache.org/docs/trunk/en/install.html).$Color_Off" >&2
    exit 1
fi

# Check libapache2-mod-wsgi-py3
if dpkg -l libapache2-mod-wsgi-py3 &>/dev/null; then
    echo "mod_wsgi:$Green OK !$Color_Off"
else
    echo "mod_wsgi:$Red ERROR - mod_wsgi must be installed." >&2
    echo "You can try 'sudo apt install libapache2-mod-wsgi-py3', or to install from the original source code, see: see: https://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html"
    exit 1
fi

# Configure Apache
echo "$Yellow"
echo "Configuring Apache2...$Color_Off"

REGEX_SITE='^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
REGEX_EMAIL='^[a-zA-Z][a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'


echo ""

while true; do
    echo -n "Please specify your server's hostname (I.E: 'www.sandbox.com'): "
    read -r URL
    if [[ $URL =~ $REGEX_SITE ]]; then
        echo -n "$Green"
        echo "The server's hostname will be '$URL'.$Color_Off"
        break
    else
        echo -n "$Red"
        echo "The server's hostname is invalid.$Color_Off"
    fi
done

echo ""

while true; do
    echo -n "Please specify your server admin's email (I.E: 'webmaster@localhost.com'): "
    read -r EMAIL
    if [[ $EMAIL =~ $REGEX_EMAIL ]]; then
        echo "The server admin's email will be '$EMAIL'.$Color_Off"
        break
    else
        echo -n "$Red"
        echo "The server admin's email is invalid.$Color_Off"
    fi
done

echo ""

echo "Creating 'sandbox-auto.conf' in etc/apache2/sites-enabled/..."
echo -e "
<VirtualHost *:80>
    ServerName $URL
    ServerAdmin $EMAIL

    ErrorLog \${APACHE_LOG_DIR}/error.log
    CustomLog \${APACHE_LOG_DIR}/access.log combined

    <Directory $PWD/>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    SetEnv PYTHONIOENCODING utf-8
    WSGIDaemonProcess sandbox $PWD/
    WSGIProcessGroup  sandbox
    WSGIScriptAlias / $PWD/wsgi.py
</VirtualHost>
" > /etc/apache2/sites-enabled/sandbox-auto.conf

echo -n "$Green"
echo "Deployment successfull$Color_Off"
echo ""
