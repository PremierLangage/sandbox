# Installation

### Requirements:

- python >= 3.5
- pip3
- docker [See Docker](https://docs.docker.com/engine/installation/linux/docker-ce/debian/)

### Installation

- Run server/serverpl/install_local.sh
- create directories *pl-sandbox/../tmp* and *pl-sandbox/../log*
- Run the server (*python manage.py runserver*)


# Logging

Default facility used for syslog is local6.
To enable logging on a custom log file, you should created a new file ending by .conf in '/etc/rsyslog.d/' containing:

  local6.*	/var/log/sandbox.log # 'replace sandbox.log with whatever you want'
  $EscapeControlCharactersOnReceive off
  & stop

And restart syslog and rsyslog services
