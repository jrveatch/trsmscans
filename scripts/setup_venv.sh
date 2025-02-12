#!/usr/bin/env sh

# minimum allowed version of python
python3_minimum="3.8"

# minimum version major and minor
python3_minimum_major=$(echo "$python3_minimum" | cut -d. -f1)
python3_minimum_minor=$(echo "$python3_minimum" | cut -d. -f2)

# get default python executable and version
python3_default_exe=$(which python3)
python3_default_version=$(python3 --version 2>&1 | cut -d' ' -f2)

# prompt user for input
printf "Your default python3 executable is $python3_default_exe (version $python3_default_version).\n"
if [ -n "$ZSH_VERSION" ]; then
    printf "Enter the python3 executable you want to use (leave blank for default): "
    read python3_exe
else
    read -p "Enter the python3 executable you want to use (leave blank for default): " python3_exe
fi

# check if the user entered something
if [ -z "$python3_exe" ]; then
    # if no input, use the default 'python3'
    python3_exe="python3"
fi

# get python3 version
python3_version=$($python3_exe --version 2>&1 | cut -d' ' -f2)

# version major and minor
python3_major=$(echo "$python3_version" | cut -d. -f1)
python3_minor=$(echo "$python3_version" | cut -d. -f2)

# print info to screen
printf "Using $python3_exe (version $python3_version)\n"

# complain and exit if python version is less than minimum
if [[ $python3_major -lt $python3_minimum_major || ($python3_major -eq $python3_minimum_major && $python3_minor -lt $python3_minimum_minor) ]]; then
    printf "Error: The specified Python3 version $python3_version is below the minimum $python3_minimum\n"
    printf "Please install $python3_minimum and try again\n"
    return 1
fi

$python3_exe -m venv trsm_venv --upgrade-deps
source trsm_venv/bin/activate
pip install -r python/requirements.txt
