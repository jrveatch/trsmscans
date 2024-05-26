
# check dependencies
source scripts/checkdeps.sh
ret=$?
if [ $ret -ne 0 ]; then
    return 1
fi

# make output directory structure
source scripts/outputdirs.sh

# set up submodules
echo "Setting up submodules"
source scripts/setup_submodules.sh

# set up python virtual environment if it doesn't exist
if [ ! -d trsm_venv ]; then
    echo "Setting up python virtual environment"
    python3 -m venv trsm_venv
    source trsm_venv/bin/activate
    pip install -r python/requirements.txt
fi

# source setup.sh to make sure all vars are set
source setup.sh

# install ScannerS and HiggsTools
echo "Compiling ScannerS and higgstools"
source scripts/compile.sh
