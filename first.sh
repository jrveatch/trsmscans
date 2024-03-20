
# set up submodules
source setupsubmodules.sh

# set up python virtual environment
python -m venv trsm_venv
pip install python/requirements.txt

# install ScannerS and HiggsTools
source compile.sh
