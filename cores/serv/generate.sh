#!/bin/bash
set -ex
rm -rf serv-src
git clone git@github.com:olofk/serv.git serv-src
python3 ../../checks/genchecks.py
