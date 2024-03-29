"""
Django settings for sandbox project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import logging
import os
import sys
import threading
import platform

from apscheduler.triggers.cron import CronTrigger
from docker.types import Ulimit


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+61drt2^c32qp)knvy32m*xm*ew=po%f8a9l!bp$kd7mz3(109'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Set to true when 'python3 manage.py test' is used
TESTING = sys.argv[1:2] == ['test']

ALLOWED_HOSTS = ['127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'sandbox',
]

MIDDLEWARE = [
    'django_http_exceptions.middleware.ExceptionHandlerMiddleware',
    'django_http_exceptions.middleware.ThreadLocalRequestMiddleware',
]

ROOT_URLCONF = 'urls'

WSGI_APPLICATION = 'wsgi.application'

# Database
DATABASES = dict()

# Needed for manage.py to run without database
TEST_RUNNER = 'testing.DatabaseLessTestRunner'

# Password validation
AUTH_PASSWORD_VALIDATORS = list()

# Write email in console instead of sending it if DEBUG is set to True
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logger information

LOGGER_ADDRESS = '/dev/log'
if platform.system() == 'Darwin':
    # https://docs.python.org/3/library/logging.handlers.html#sysloghandler
    LOGGER_ADDRESS = '/var/run/syslog'

LOGGING = {
    'version':                  1,
    'disable_existing_loggers': False,
    'filters':                  {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true':  {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters':               {
        'verbose': {
            'format':  ("[%(asctime)-15s] [%(pathname)s]"
                        "[%(filename)s:%(funcName)s:%(lineno)d]"
                        " %(levelname)s -- %(message)s"),
            'datefmt': '%Y/%m/%d %H:%M:%S'
        },
        'simple':  {
            'format':  ("[%(asctime)s] [%(filename)s:%(funcName)s:%(lineno)d]"
                        " %(levelname)s -- %(message)s"),
            'datefmt': '%H:%M:%S'
        },
    },
    'handlers':                 {
        'console':      {
            'level':     'DEBUG',
            'class':     'logging.StreamHandler',
            'formatter': 'simple'
        },
        'syslog':       {
            'level':     'INFO',
            'class':     'logging.handlers.SysLogHandler',
            'facility':  'local6',
            'address':   LOGGER_ADDRESS,
            'formatter': 'verbose',
            'filters':   ['require_debug_false'],
        },
        'syslog_debug': {
            'level':     'DEBUG',
            'class':     'logging.handlers.SysLogHandler',
            'facility':  'local6',
            'address':   LOGGER_ADDRESS,
            'formatter': 'verbose',
            'filters':   ['require_debug_true'],
        },
        'mail_admins':  {
            'level':        'WARNING',
            'class':        'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'formatter':    'verbose'
        }
    },
    'loggers':                  {
        'sandbox':        {
            'handlers':  ['console', 'syslog', 'mail_admins', 'syslog_debug'],
            'level':     'DEBUG',
            'propagate': True,
        },
        'django':         {
            'handlers': ['console', 'syslog', 'mail_admins', 'syslog_debug'],
            'level':    'INFO',
        },
        'django.request': {
            'handlers':  ['console', 'syslog', 'syslog_debug'],
            'level':     'WARNING',
            'propagate': False,
        }
    },
}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'

# External libraries will be added to containers in /utils/libs/, this directory will be added
# to both PATH and PYTHONPATH environment variables.
# Each external lib must be a tuple (GIT_URL, ALIAS), where GIT_URL is the URL 'git clone'
# will use, ALIAS the directory in which the library will be cloned.
EXTERNAL_LIBRARIES = [
    ("https://github.com/PremierLangage/premierlangage-lib.git", "pl"),
]

# Path where the libraries are downloaded
EXTERNAL_LIBRARIES_ROOT = os.path.join(BASE_DIR, 'libs')
if not os.path.isdir(EXTERNAL_LIBRARIES_ROOT):
    os.makedirs(EXTERNAL_LIBRARIES_ROOT)

# The CronTrigger triggering the update of the external libraries, see
# https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html for more information.
EXTERNAL_LIBRARIES_CRON_TRIGGER = CronTrigger(
    year="*",
    month="*",
    day="*",
    week="*",
    day_of_week="*",
    hour="*/2",
    minute="0",
    second="0",
)

SANDBOX_VERSION = "3.0.3"

# Time before returning a '503: Service Unavailable' when waiting for a container.
WAIT_FOR_CONTAINER_DURATION = 2

# Total time for an '/execute/' request before timeout
EXECUTE_TIMEOUT = 10.0

# Directory where environments are stored
ENVIRONMENT_ROOT = os.path.join(BASE_DIR, 'environments')
if not os.path.isdir(ENVIRONMENT_ROOT):
    os.makedirs(ENVIRONMENT_ROOT)

# ENVIRONMENT_EXPIRATION: Time before the environment are deleted.
HOUR = 3600
DAY = HOUR * 24
ENVIRONMENT_EXPIRATION = DAY

#
# DOCKER_COUNT (int) – Max number of containers running simultaneously.
# DOCKER_VOLUME_MEM_LIMIT (int) – Limit of memory usage for volumes (in MB).
# DOCKER_VOLUME_HOST_BASEDIR (str) – Path to the root directory containing each directory shared
#       with the containers. For each container, a directory named after the container's name is
#       created inside DOCKER_VOLUME_HOST_BASEDIR.
#
# DOCKER_PARAMETERS (dict) - kwargs given to the Containers constructor. See
# https://docker-py.readthedocs.io/en/stable/containers.html and
# https://docs.docker.com/config/containers/resource_constraints/ for more information about
# every argument
DOCKER_COUNT = 20
DOCKER_VOLUME_HOST_BASEDIR = os.path.join(BASE_DIR, 'containers_env')
DOCKER_PARAMETERS = {
    "image":            "pl:latest",
    "auto_remove":      True,
    "cpu_period":       1000,
    "cpu_shares":       1024,
    "cpu_quota":        0,
    "cpuset_cpus":      "0",
    "detach":           True,
    "environment":      {},
    "mem_limit":        "100m",
    "memswap_limit":    "200m",
    "network_mode":     "none",
    "network_disabled": True,
    # "storage_opt":      {},
    "tty":              True,
    "ulimits":          [
        Ulimit(name="core", soft=0, hard=0)
    ],
}

# Check if any of the above settings are override by a config.py file.
logger = logging.getLogger(__name__)
try:
    from config import *  # noqa
    logger.info("Using config.py...")
except ModuleNotFoundError:
    logger.info("No config file found")
del logger

# Override some settings from testing purpose
if TESTING:
    DOCKER_COUNT = 5

from sandbox.containers import initialise_containers  # noqa


INITIALISING_THREAD = threading.Thread(target=initialise_containers)
INITIALISING_THREAD.start()
