#!/bin/bash -e

docker ps --filter name="c[0-9]+" --filter status=running -aq | xargs docker stop 2>/dev/null
