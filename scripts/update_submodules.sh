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
        printf "Checking for updates to $submodule...\n"
        
        # Fetch the latest changes
        git submodule update --remote --merge "$submodule"
        
        # Check if there are new commits
        if ! git diff --quiet HEAD "$submodule"; then
            printf "$submodule was updated. Checking out changes...\n"
            git -C "$submodule" checkout origin/main  # Adjust branch if needed
            printf "Success!\n"
            
            # If a compile script is provided, execute it
            if [ -n "$compile_script" ]; then
                printf "Compiling $submodule...\n"
                "$compile_script"
            fi
        fi
    else
        printf "Skipping $submodule update (using external path: ${!path_var})\n"
    fi
}

# Update ScannerS if SCANNERS_PATH is not set
update_submodule "externals/ScannerS" "SCANNERS_PATH" "scripts/compile_scanners.sh"

# Update HiggsTools if HIGGSTOOLS_PATH is not set
update_submodule "externals/higgstools" "HIGGSTOOLS_PATH" "scripts/compile_higgstools.sh"

# Function to update submodules without compilation
update_data_submodule() {
    local submodule="$1"
    local path_var="$2"
    
    if [ -z "${!path_var:-}" ]; then
        printf "Checking for updates to $submodule...\n"
        git submodule update --remote --merge "$submodule"
    else
        printf "Skipping $submodule update (using external path: ${!path_var})\n"
    fi
}

# Update data submodules if not stored in env.sh
update_data_submodule "externals/hbdataset" "HBDATASET_PATH"
update_data_submodule "externals/hsdataset" "HSDATASET_PATH"

printf "All submodules are updated to the latest versions\n\n"
