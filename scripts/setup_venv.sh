
# get default python executable and version
python3_default_exe=$(which python3)
python3_default_version=$(python3 --version 2>&1 | cut -d' ' -f2)

# prompt user for input
printf "Your default python3 executable is $python3_default_exe (version $python3_default_version)."
if [ -n "$ZSH_VERSION" ]; then
    printf "Enter the python3 executable you want to use (leave blank for default):"
    read python3_exe
else
    read -p "Enter the python3 executable you want to use (leave blank for default): " python3_exe
fi

# check if the user entered something
if [ -z "$python3_exe" ]; then
    # if no input, use the default 'python3'
    python3_exe="python3"
fi

# get python3 version
python3_version=$($python3_exe --version 2>&1 | cut -d' ' -f2)

# print info to screen
printf "Using $python3_exe (version $python3_version)"

$python3_exe -m venv trsm_venv
source trsm_venv/bin/activate
pip install -r python/requirements.txt
