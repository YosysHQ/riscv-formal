#!/bin/bash
set -ex
rm -rf ridecore-src checks
git clone https://github.com/gipsyh/ridecore-rvfi.git ridecore-src
python3 ../../checks/genchecks.py
