#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Minimum Python and CMake versions
python3_minimum="3.8"
cmake_minimum="3.17"

# Minimum majors and minors
python3_minimum_major=$(echo "$python3_minimum" | cut -d. -f1)
python3_minimum_minor=$(echo "$python3_minimum" | cut -d. -f2)
cmake_minimum_major=$(echo "$cmake_minimum" | cut -d. -f1)
cmake_minimum_minor=$(echo "$cmake_minimum" | cut -d. -f2)

###########################################
# Python
###########################################

# Check to make sure a version of Python3 is installed
if ! command -v python3 &> /dev/null
then
  printf "Python3 is not installed. Please install $python3_minimum or newer and try again\n"
  exit 1
fi

# Get the Python3 version
python3_version=$(python3 --version 2>&1 | cut -d' ' -f2)

# Extract major and minor version numbers
python3_major=$(echo "$python3_version" | cut -d. -f1)
python3_minor=$(echo "$python3_version" | cut -d. -f2)

# Check if Python version is less than minimum
if [[ $python3_major -lt $python3_minimum_major || ($python3_major -eq $python3_minimum_major && $python3_minor -lt $python3_minimum_minor) ]]; then
    printf "Warning: Your default Python3 version $python3_version is below the minimum $python3_minimum\n"
    printf "Warning: You may need to specify a separate installation when setting up the venv\n"
fi

###########################################
# CMake
###########################################

# Make sure cmake is installed
if ! command -v cmake &> /dev/null; then
  printf "Error: CMake is not installed. Please install CMake $cmake_minimum or newer and try again\n"
  exit 1
fi

# Get the CMake version
cmake_version=$(cmake --version 2>&1 | head -n 1 | cut -d' ' -f3)

# Extract major and minor version numbers
cmake_major=$(echo "$cmake_version" | cut -d. -f1)
cmake_minor=$(echo "$cmake_version" | cut -d. -f2)

# Check if CMake version is less than minimum
if [[ $cmake_major -lt $cmake_minimum_major || ($cmake_major -eq $cmake_minimum_major && $cmake_minor -lt $cmake_minimum_minor) ]]; then
    printf "Error: CMake version $cmake_version is below $cmake_minimum\n"
    printf "Please install $cmake_minimum and try again\n"
    exit 1
fi

printf "CMake version $cmake_version is installed\n" 

printf "All dependencies are installed and meet the minimum version requirements\n"

