#!/usr/bin/env sh

set -e
set -u
set -o pipefail

# check dependencies
if ! bash scripts/check_deps.sh; then
    echo "Error: check_deps.sh failed!" >&2
    return 1
fi

# set user paths
printf "Setting up user paths\n"
source scripts/set_user_paths.sh

# set up submodules
printf "Setting up submodules\n"
./scripts/setup_submodules.sh

# set up python virtual environment if it doesn't exist
if [ ! -d trsm_venv ]; then
    printf "Setting up python virtual environment\n"
    ./scripts/setup_venv.sh
fi

# source setup.sh to make sure all vars are set
source setup.sh

# install ScannerS and HiggsTools
printf "Compiling ScannerS and higgstools\n"
source scripts/compile.sh
