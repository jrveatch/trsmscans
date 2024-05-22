#!/bin/bash

# start python virtual environment
source scripts/venv.sh

# add path to executable to PATH
export PATH="${PWD}/ScannerS/build:$PATH"

# set data directory as environment variable
export DATADIR="${PWD}/data/"

# set data directory as environment variable
export RUNDIR="${PWD}/data/"

# set output directory as environment variable
export OUTPUTDIR="${RUNDIR}/output/"

# set prescan directory as environment variable
export PRESCANDIR="${OUTPUTDIR}/prescan/"

# set scan directory as environment variable
export SCANDIR="${OUTPUTDIR}/scan/"

# set plot directory as environment variable
export PLOTDIR="${OUTPUTDIR}/plots/"
