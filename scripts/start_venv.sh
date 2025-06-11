#!/usr/bin/env bash

# source env.sh to load existing environment variables
if [ -f env.sh ]; then
    source env.sh
fi

# start the python virtual environment
printf "\nActivating venv\n"
source $TRSM_VENV_PATH/bin/activate

# check whether requirements file exists
if ! [ -f "python/requirements.txt" ]; then
    printf "python/requirements.txt not found\n"
    return 1
fi

# try to update all packages and only print the lines that are not already satisfied
printf "\nUpdating python packages...\n"
pip install -r "python/requirements.txt" | grep -v 'Requirement already satisfied' || true
printf "Packages are all up to date\n"
