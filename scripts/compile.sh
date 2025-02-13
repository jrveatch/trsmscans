#!/bin/bash

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

echo "Compiling with $CORES_TO_USE threads..."

# compile ScannerS
printf "\n"
printf "Trying to compile ScannerS"
printf "\n"
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make -j"$CORES_TO_USE"
cd ../..

# compile higgstools with C++
printf "\n"
printf "Trying to compile higgstools"
printf "\n"
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make -j"$CORES_TO_USE"
cd ../..

# compile higgstools python module
printf "\n"
printf "Trying to compile higgstools python"
printf "\n"
cd higgstools
MAKEFLAGS="-j$CORES_TO_USE" pip install .
cd ..
