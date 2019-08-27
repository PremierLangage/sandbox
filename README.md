[![Build Status](https://travis-ci.org/qcoumes/sandbox.svg?branch=master)](https://travis-ci.org/qcoumes/sandbox)
[![codecov](https://codecov.io/gh/qcoumes/sandbox/branch/master/graph/badge.svg)](https://codecov.io/gh/qcoumes/sandbox)
[![CodeFactor](https://www.codefactor.io/repository/github/qcoumes/sandbox/badge)](https://www.codefactor.io/repository/github/qcoumes/sandbox)
[![Documentation](https://img.shields.io/badge/docs-passing-brightgreen.svg)](https://documenter.getpostman.com/view/7955851/S1a915EG?version=latest)
[![Python 3.5+](https://img.shields.io/badge/python-3.5+-brightgreen.svg)](#)
[![License MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/qcoumes/sandbox/blob/master/LICENSE)
 
# Installation

## Requirements:

- [python >= 3.7](https://www.python.org/)
- [pip3](https://pip.pypa.io/en/stable/installing/)
- [docker](https://docs.docker.com/engine/installation/linux/docker-ce/debian/)

## Installation

Installing the server is pretty straightforward, you just need to clone the repository and run
the install script :

```bash
git clone https://github.com/PremierLangage/sandbox.git
cd sanbox
./bin/install.sh  
```

If you also want to deploy the server, run `./bin/deploy.sh`. You may want to check
the created config file at `/etc/apache2/sites-enabled/sandbox-auto.conf`.

You will then have to restart apache2 : `systemctl restart apache2` or `service apache2 restart`.


## Documentation

The API documentation is available [here](https://documenter.getpostman.com/view/7955851/S1a915EG?version=latest).
