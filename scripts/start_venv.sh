#!/usr/bin/env sh

# start the python virtual environment
printf "Activating venv\n"
source trsm_venv/bin/activate

# check whether requirements file exists
if ! [ -f "python/requirements.txt" ]; then
    printf "python/requirements.txt not found\n"
    return
fi

# try to update all packages and only print the lines that are not already satisfied
printf "Updating packages...\n"
pip install -r "python/requirements.txt" | grep -v 'Requirement already satisfied'
printf "Packages are all up to date\n"
