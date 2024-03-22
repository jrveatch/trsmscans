
if [ -d trsm_venv ]; then
    echo "Already called this script. Perhaps you want to call setup.sh instead?"
    return
fi

# set up submodules
echo "Setting up submodules"
source scripts/setupsubmodules.sh

# set up python virtual environment
echo "Setting up python virtual environment"
python3 -m venv trsm_venv
source trsm_venv/bin/activate
pip install -r python/requirements.txt

# install ScannerS and HiggsTools
echo "Compiling ScannerS and higgstools"
source scripts/compile.sh
