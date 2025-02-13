#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Minimum Python and CMake versions
python3_minimum="3.8"
cmake_minimum="3.17"

# Function to check if an installed version is less than the required version
version_less_than() {
  local installed_version=$1
  local required_version=$2

  local installed_major=$(echo "$installed_version" | awk -F. '{print $1}')
  local installed_minor=$(echo "$installed_version" | awk -F. '{print $2}')
  local required_major=$(echo "$required_version" | awk -F. '{print $1}')
  local required_minor=$(echo "$required_version" | awk -F. '{print $2}')

  [[ $installed_major -lt $required_major ]] || 
  { [[ $installed_major -eq $required_major ]] && [[ $installed_minor -lt $required_minor ]]; }
}

###########################################
# Python
###########################################

# Check to make sure a version of Python3 is installed
if ! command -v python3 &> /dev/null; then
  printf "Error: Python3 is not installed. Please install version %s or newer.\n" "$python3_minimum"
  exit 1
fi

# Get the Python3 version
python3_version=$(python3 --version 2>&1 | awk '{print $2}')

# Check if Python version is less than minimum
if version_less_than "$python3_version" "$python3_minimum"; then
  printf "Warning: Your default Python3 version (%s) is below the minimum (%s)\n" "$python3_version" "$python3_minimum"
  printf "You may need to specify an alternative installation when setting up the virtual environment.\n"
  printf "You can upgrade Python3 using:\n"
  printf "  - pyenv (https://github.com/pyenv/pyenv)\n"
  printf "  - Your package manager (apt, dnf, brew, etc.)\n"
fi

printf "Python version $python3_version is installed\n" 

###########################################
# CMake
###########################################

# Make sure cmake is installed
if ! command -v cmake &> /dev/null; then
  printf "Error: CMake is not installed. Please install CMake $cmake_minimum or newer and try again\n"
  exit 1
fi

# Get the CMake version
cmake_version=$(cmake --version 2>&1 | awk 'NR==1 {print $3}')

# Check if CMake version is less than minimum
if version_less_than "$cmake_version" "$cmake_minimum"; then
  printf "Error: CMake version (%s) is below the required minimum (%s)\n" "$cmake_version" "$cmake_minimum"
  printf "Please install CMake %s or newer from https://cmake.org/download/\n" "$cmake_minimum"
  exit 1
fi

printf "CMake version $cmake_version is installed\n" 

printf "All dependencies are installed and meet the minimum version requirements\n"

