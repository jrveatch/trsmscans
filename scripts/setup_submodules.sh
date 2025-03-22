#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Set environment variables from env.sh if it exists
if [ -f env.sh ]; then
    source env.sh
fi

# Check if SCANNERS_PATH is set, if so, skip ScannerS submodule
if [ -z "${SCANNERS_PATH:-}" ]; then
    printf "Initializing and updating ScannerS submodule...\n"
    git submodule update --init --recursive externals/ScannerS
else
    printf "Skipping ScannerS submodule as SCANNERS_PATH is set to $SCANNERS_PATH\n"
fi

# Check if HIGGSTOOLS_PATH is set, if so, skip HiggsTools submodule
if [ -z "${HIGGSTOOLS_PATH:-}" ]; then
    printf "Initializing and updating HiggsTools submodule...\n"
    git submodule update --init --recursive externals/higgstools
else
    printf "Skipping HiggsTools submodule as HIGGSTOOLS_PATH is set to $HIGGSTOOLS_PATH\n"
fi

# Check if HBDATASET_PATH is set, if so, skip HBDataSet submodule
if [ -z "${HBDATASET_PATH:-}" ]; then
    printf "Initializing and updating HBDataSet submodule...\n"
    git submodule update --init --recursive data/hbdataset
else
    printf "Skipping HBDataSet submodule as HBDATASET_PATH is set to $HBDATASET_PATH\n"
fi

# Check if HSDATASET_PATH is set, if so, skip HSDataSet submodule
if [ -z "${HSDATASET_PATH:-}" ]; then
    printf "Initializing and updating HSDataSet submodule...\n"
    git submodule update --init --recursive data/hsdataset
else
    printf "Skipping HSDataSet submodule as HSDATASET_PATH is set to $HSDATASET_PATH\n"
fi

# Create a file to indicate that submodules are set up
touch .submodules_ok
