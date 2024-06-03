
# check dependencies
source scripts/checkdeps.sh
ret=$?
if [ $ret -ne 0 ]; then
    return 1
fi

# set up submodules
echo "Setting up submodules"
source scripts/setup_submodules.sh

# set up python virtual environment if it doesn't exist
if [ ! -d trsm_venv ]; then
    echo "Setting up python virtual environment"
    source scripts/setup_venv.sh
fi

# source setup.sh to make sure all vars are set
source setup.sh

# install ScannerS and HiggsTools
echo "Compiling ScannerS and higgstools"
source scripts/compile.sh
