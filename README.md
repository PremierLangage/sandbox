# Installation

### Requirements:

- python >= 3.5
- pip3
- docker [See Docker](https://docs.docker.com/engine/installation/linux/docker-ce/debian/)

### Installation

- Run server/serverpl/install.sh
- (deprecated : premierlangage has its own sandbox) Run the server (*python3 manage.py runserver [port]*)
- make visible with apache 


# Logging

Default facility used for syslog is local6.
To enable logging on a custom log file, you should created a new file ending by .conf in '/etc/rsyslog.d/' containing:

```
local6.*	/var/log/sandbox.log # 'replace sandbox.log with whatever you want'
$EscapeControlCharactersOnReceive off
& stop
```

And restart syslog and rsyslog services
