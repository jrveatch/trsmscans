#!/usr/bin/env sh

# start python virtual environment
source scripts/start_venv.sh

# update submodules
if ! bash scripts/update_submodules.sh; then
    echo "Error: update_submodules.sh failed!" >&2
    return 1
fi

# Source env.sh to load existing environment variables
if [ -f env.sh ]; then
    source env.sh
fi
