#!/bin/bash

# start python virtual environment
source scripts/venv.sh

# add path to executable to PATH
export PATH="${PWD}/ScannerS/build:$PATH"

# set data directory as environment variable
export DATADIR="${PWD}/data/"

# set prescan directory as environment variable
export PRESCANDIR="${PWD}/run/output/prescan/"

# set scan directory as environment variable
export SCANDIR="${PWD}/run/output/scan/"
