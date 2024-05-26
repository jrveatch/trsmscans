#!/bin/bash

# start python virtual environment
source scripts/venv.sh

# add path to executable to PATH
export PATH="${PWD}/ScannerS/build:$PATH"

# set data directory as environment variable
export DATADIR="${PWD}/data/"

# set run directory as environment variable
export RUNDIR="${PWD}/run/"

# set output directory as environment variable
export OUTPUTDIR="${RUNDIR}output/"
