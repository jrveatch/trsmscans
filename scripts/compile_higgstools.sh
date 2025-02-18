#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# source env.sh if it exists
if [ -f "env.sh" ]; then
  source env.sh
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

# compile HiggsTools python module
printf "\nTrying to pip install HiggsTools\n"
# Check if HIGGSTOOLS_PATH is set
if [ -n "${HIGGSTOOLS_PATH:-}" ]; then
  # Install from the provided path
  MAKEFLAGS="-j$CORES_TO_USE" pip install --no-deps "$HIGGSTOOLS_PATH"
else
  # Normal pip install for submodule
  MAKEFLAGS="-j$CORES_TO_USE" pip install ./externals/higgstools
fi
