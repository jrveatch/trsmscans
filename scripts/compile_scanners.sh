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
  printf "A pre-compiled version of ScannerS is being used. Skipping ScannerS compilation.\n"
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
printf "\nTrying to compile ScannerS with $CORES_TO_USE threads...\n"
cd externals/ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build

CMAKE_ARGS=(
  -DCMAKE_CXX_STANDARD=17
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
  -Wno-dev
)

add_eigen3_dir_if_valid() {
  local candidate="$1"

  if [[ -f "$candidate/Eigen3Config.cmake" ]]; then
    CMAKE_ARGS+=("-DEigen3_DIR=$candidate")
    printf "Using Eigen3 CMake config: %s\n" "$candidate"
    return 0
  fi

  return 1
}

if [[ -n "${EIGEN3_DIR:-}" ]]; then
  add_eigen3_dir_if_valid "$EIGEN3_DIR" || {
    printf "Error: EIGEN3_DIR is set, but Eigen3Config.cmake was not found in:\n  %s\n" "$EIGEN3_DIR"
    exit 1
  }

elif [[ "$(uname)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
  EIGEN3_PREFIX="$(brew --prefix eigen@3 2>/dev/null || true)"

  if [[ -n "$EIGEN3_PREFIX" ]]; then
    add_eigen3_dir_if_valid "$EIGEN3_PREFIX/share/eigen3/cmake" || true
  fi

else
  for candidate in \
    /usr/lib/cmake/eigen3 \
    /usr/lib64/cmake/eigen3 \
    /usr/share/eigen3/cmake \
    /usr/local/share/eigen3/cmake \
    /usr/local/lib/cmake/eigen3
  do
    add_eigen3_dir_if_valid "$candidate" && break
  done
fi

cmake "${CMAKE_ARGS[@]}" ..
make -j"$CORES_TO_USE"
cd ../../..
