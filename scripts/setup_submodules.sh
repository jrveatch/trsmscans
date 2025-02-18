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
    echo "Initializing and updating ScannerS submodule..."
    git submodule update --init --recursive externals/ScannerS
else
    echo "Skipping ScannerS submodule as SCANNERS_PATH is set to $SCANNERS_PATH"
fi

# Check if HIGGSTOOLS_PATH is set, if so, skip HiggsTools submodule
if [ -z "${HIGGSTOOLS_PATH:-}" ]; then
    echo "Initializing and updating HiggsTools submodule..."
    git submodule update --init --recursive externals/higgstools
else
    echo "Skipping HiggsTools submodule as HIGGSTOOLS_PATH is set to $HIGGSTOOLS_PATH"
fi

# Check if HBDATASET_PATH is set, if so, skip HBDataSet submodule
if [ -z "${HBDATASET_PATH:-}" ]; then
    echo "Initializing and updating HBDataSet submodule..."
    git submodule update --init --recursive data/hbdataset
else
    echo "Skipping HBDataSet submodule as HBDATASET_PATH is set to $HBDATASET_PATH"
fi

# Check if HSDATASET_PATH is set, if so, skip HSDataSet submodule
if [ -z "${HSDATASET_PATH:-}" ]; then
    echo "Initializing and updating HSDataSet submodule..."
    git submodule update --init --recursive data/hsdataset
else
    echo "Skipping HSDataSet submodule as HSDATASET_PATH is set to $HSDATASET_PATH"
fi

# Create a file to indicate that submodules are set up
touch .submodules_ok
