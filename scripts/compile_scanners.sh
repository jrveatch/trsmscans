#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# source env.sh if it exists
if [ -f "env.sh" ]; then
  source env.sh
fi

# skip compilation if SCANNERS_PATH is set
if [ -n "${SCANNERS_PATH:-}" ]; then
  echo "A pre-compiled version of ScannerS is being used. Skipping ScannerS compilation."
  exit 0
fi

# get total number of CPU cores
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
