
# set up submodules
source scripts/setupsubmodules.sh

# set up python virtual environment
python3 -m venv trsm_venv
pip install -r python/requirements.txt

# install ScannerS and HiggsTools
source scripts/compile.sh
