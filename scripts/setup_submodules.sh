#!/usr/bin/env sh

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
    git submodule update --init --recursive ScannerS
else
    echo "Skipping ScannerS submodule as SCANNERS_PATH is set to $SCANNERS_PATH"
fi

# Check if HIGGSTOOLS_PATH is set, if so, skip higgstools submodule
if [ -z "${HIGGSTOOLS_PATH:-}" ]; then
    echo "Initializing and updating higgstools submodule..."
    git submodule update --init --recursive higgstools
else
    echo "Skipping higgstools submodule as HIGGSTOOLS_PATH is set to $HIGGSTOOLS_PATH"
fi