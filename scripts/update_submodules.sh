#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Source environment variables
if [ -f env.sh ]; then
    source env.sh
fi

# Function to update a submodule if no external path is set
update_submodule() {
    local submodule="$1"
    local path_var="$2"
    local compile_script="$3"

    if [ -z "${!path_var:-}" ]; then
        echo "Checking for updates to $submodule..."
        
        # Fetch the latest changes
        git submodule update --remote --merge "$submodule"
        
        # Check if there are new commits
        if git diff --quiet HEAD "$submodule"; then
            echo "$submodule is already up to date."
        else
            echo "$submodule was updated. Checking out changes..."
            git -C "$submodule" checkout origin/main  # Adjust branch if needed
            
            # If a compile script is provided, execute it
            if [ -n "$compile_script" ]; then
                echo "Compiling $submodule..."
                "$compile_script"
            fi
        fi
    else
        echo "Skipping $submodule update (using external path: ${!path_var})"
    fi
}

# Update ScannerS if SCANNERS_PATH is not set
update_submodule "externals/ScannerS" "SCANNERS_PATH" "scripts/compile_scanners.sh"

# Update HiggsTools if HIGGSTOOLS_PATH is not set
update_submodule "externals/HiggsTools" "HIGGSTOOLS_PATH" "scripts/compile_higgstools.sh"

# Function to update submodules without compilation
update_data_submodule() {
    local submodule="$1"
    local path_var="$2"
    
    if [ -z "${!path_var:-}" ]; then
        echo "Checking for updates to $submodule..."
        git submodule update --remote --merge "$submodule"
    else
        echo "Skipping $submodule update (using external path: ${!path_var})"
    fi
}

# Update data submodules if not stored in env.sh
update_data_submodule "data/hbdataset" "HBDATASET_PATH"
update_data_submodule "data/hsdataset" "HSDATASET_PATH"


printf "All submodules are updated to the latest versions\n"
