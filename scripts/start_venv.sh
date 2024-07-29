#!/bin/bash

# deactivate any previously activated virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]
then
    deactivate
fi

# start the python virtual environment
source trsm_venv/bin/activate

# check whether requirements file exists
if ! [ -f "python/requirements.txt" ]; then
    echo "python/requirements.txt not found."
    return
fi

# create temporary files for storing pip freeze output
installed_packages_temp=$(mktemp)
requirements_temp=$(mktemp)

# capture the current installed packages using pip freeze
pip freeze > "$installed_packages_temp"

# get list of packages from pip freeze that are not in requirements.txt
comm -13 "$installed_packages_temp" "python/requirements.txt" > "$requirements_temp"

# check if there are any differences between installed packages and requirements
if [ -s "$requirements_temp" ]; then
    echo "Requirements file has changed"
    cat "$requirements_temp"
    echo "Updating packages..."
    pip install -r "$requirements_temp"
    echo "Packages updated"
else
    echo "Python packages are all up-to-date"
fi

# clean up temporary files
rm -rf "$installed_packages_temp" "$requirements_temp"
