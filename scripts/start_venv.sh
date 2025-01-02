#!/bin/bash

# deactivate any previously activated virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]
then
    printf "Deactivating previous venv\n"
    ( deactivate )
fi

# start the python virtual environment
printf "Activating venv\n"
source trsm_venv/bin/activate

# check whether requirements file exists
if ! [ -f "python/requirements.txt" ]; then
    printf "python/requirements.txt not found\n"
    return
fi

# create temporary files for storing package versions
installed_packages_temp=$(mktemp)
normalized_requirements_temp=$(mktemp)
requirements_temp=$(mktemp)

# normalize requirements file
cat python/requirements.txt | tr '[:upper:]' '[:lower:]' | sort > "$normalized_requirements_temp"

# capture the current installed packages using pip freeze
pip freeze | tr '[:upper:]' '[:lower:]' | sort > "$installed_packages_temp"

# get list of packages from pip freeze that are not in requirements.txt
comm -13 "$installed_packages_temp" "$normalized_requirements_temp" > "$requirements_temp"

# check if there are any differences between installed packages and requirements
if [ -s "$requirements_temp" ]; then
    printf "Requirements file has changed\n"
    cat "$requirements_temp"
    printf "Updating packages...\n"
    pip install -r "$requirements_temp"
    printf "Packages updated\n"
else
    printf "Python packages are all up-to-date\n"
fi

# clean up temporary files
rm -rf "$installed_packages_temp" "$requirements_temp"
