#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# get total umber of CPU cores
if [[ "$(uname)" == "Darwin" ]]; then
  # macOS
  TOTAL_CORES=$(sysctl -n hw.ncpu)
else
  # Linux
  TOTAL_CORES=$(nproc)
fi

# use all but one core in compilation, unless only one is available
CORES_TO_USE=$(( TOTAL_CORES > 1 ? TOTAL_CORES - 1 : 1 ))

# compile ScannerS
printf "Trying to compile ScannerS $CORES_TO_USE threads...\n"
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make -j"$CORES_TO_USE"
cd ../..
