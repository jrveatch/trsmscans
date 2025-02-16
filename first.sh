#!/usr/bin/env sh

# check dependencies
if ! bash scripts/check_deps.sh; then
    echo "Error: check_deps.sh failed!" >&2
    return 1
fi

# set user paths
printf "Setting up user paths\n"
if ! bash scripts/set_user_paths.sh; then
    echo "Error: set_user_paths.sh failed!" >&2
    return 1
fi

# set up submodules
printf "Setting up submodules\n"
if ! bash scripts/setup_submodules.sh; then
    echo "Error: setup_submodules.sh failed!" >&2
    return 1
fi

# set up python virtual environment if it doesn't exist
if [ ! -d trsm_venv ]; then
    printf "Setting up python virtual environment\n"
    if ! bash scripts/setup_venv.sh; then
        echo "Error: setup_venv.sh failed!" >&2
        return 1
    fi
fi

# source setup.sh to make sure all vars are set
source setup.sh

# install ScannerS and HiggsTools
if ! bash scripts/compile_scanners.sh; then
    echo "Error: compile_scanners.sh failed!" >&2
    return 1
fi

if ! bash scripts/compile_higgstools.sh; then
    echo "Error: compile_higgstools.sh failed!" >&2
    return 1
fi
