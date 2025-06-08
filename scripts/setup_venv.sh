#!/usr/bin/env sh

# source env.sh to load existing environment variables
if [ -f env.sh ]; then
    source env.sh
fi

# create the virtual environment
$PYTHON3_EXE -m venv trsm_venv --upgrade-deps

# add the virtual environment to env.sh
echo "export TRSM_VENV_PATH=\"$(pwd)/trsm_venv\"" >> env.sh

printf "Virtual environment trsm_venv successfully created\n"
