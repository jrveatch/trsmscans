#!/usr/bin/env sh

# start python virtual environment
source scripts/start_venv.sh

# update submodules
source scripts/update_submodules.sh

# add path to ScannerS executable to PATH
export PATH="${PWD}/ScannerS/build:$PATH"

# set data directory as environment variable
export DATADIR="${PWD}/data/"

# set config directory as environment variable
export CONFIGDIR="${PWD}/config/"

# set run directory as environment variable
export RUNDIR="${PWD}/run/"

# set output directory as environment variable
export OUTPUTDIR="${RUNDIR}output/"
