#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Minimum Python and CMake versions
python3_minimum="3.8"
cmake_minimum="3.17"

# get useful functions
source ./scripts/functions.sh

###########################################
# Python
###########################################

# Check to make sure a version of Python3 is installed
if ! command -v python3 &> /dev/null; then
  printf "Error: Python3 is not installed. Please install version %s or newer.\n" "$python3_minimum" >&2
  exit 1
fi

# get default python executable and version
python3_default_exe=$(which python3)
python3_default_version=$(python3 --version 2>&1 | awk '{print $2}')

# prompt user for input
printf "\nYour default python3 executable is $python3_default_exe (version $python3_default_version).\n\n"
printf "Enter the python3 executable you want to use (leave blank for default): "
read python3_exe

# check if the user entered something
if [ -z "$python3_exe" ]; then
    # if no input, use the default 'python3'
    python3_exe="python3"
fi

# get python3 version
python3_version=$($python3_exe --version 2>&1 | awk '{print $2}')

# Check if Python version is less than minimum
if version_less_than "$python3_version" "$python3_minimum"; then
  printf "Error: The specified Python3 version $python3_version is below the minimum $python3_minimum\n"
  printf "Please try again after installing >= $python3_minimum using:\n"
  printf "  - pyenv (https://github.com/pyenv/pyenv)\n" >&2
  printf "  - Your package manager (apt, dnf, brew, etc.)\n" >&2
  exit 1
fi

# Remove previous entry in env.sh
remove_var_from_env "PYTHON3_EXE"

# Store python3 exe in env.sh
if [ "$python3_exe" != "python3" ]; then
  echo "export PYTHON3_EXE=\"${python3_exe}\"" >> env.sh
fi

printf "Python version $python3_version is installed (>= $python3_minimum)\n" 

###########################################
# CMake
###########################################

# Make sure cmake is installed
if ! command -v cmake &> /dev/null; then
  printf "Error: CMake is not installed. Please install CMake %s or newer and try again\n" "$cmake_minimum" >&2
  exit 1
fi

# Get the CMake version
cmake_version=$(cmake --version 2>&1 | awk 'NR==1 {print $3}')

# Check if CMake version is less than minimum
if version_less_than "$cmake_version" "$cmake_minimum"; then
  printf "Error: CMake version (%s) is below the required minimum (%s)\n" "$cmake_version" "$cmake_minimum" >&2
  printf "Please install CMake %s or newer from https://cmake.org/download/\n" "$cmake_minimum" >&2
  exit 1
fi

printf "CMake version $cmake_version is installed (>= $cmake_minimum)\n"

# Check compilers
if ! bash scripts/check_compilers.sh; then
    echo "Error: check_compilers.sh failed!" >&2
    exit 1
fi

# Create file to indicate that all dependencies have been successfully checked
touch .deps_ok

printf "All dependencies are installed and meet the minimum version requirements\n"
