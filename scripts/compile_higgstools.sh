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

# compile HiggsTools with C++
printf "Trying to compile HiggsTools with $CORES_TO_USE threads...\n"
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make -j"$CORES_TO_USE"
cd ../..

# compile HiggsTools python module
printf "Trying to pip install HiggsTools\n"
cd higgstools
MAKEFLAGS="-j$CORES_TO_USE" pip install .
cd ..
