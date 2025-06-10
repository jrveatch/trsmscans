#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# get useful functions
source ./scripts/functions.sh

# Source env.sh to load existing environment variables
if [ -f env.sh ]; then
    source env.sh
else
    touch env.sh  # Create env.sh if it doesn't exist
fi

# Function to convert relative path to absolute path
get_absolute_path() {
    local input_path="$1"

    # If the path is already absolute, return it as-is
    case "$input_path" in
        /*) echo "$input_path"; return ;;
    esac

    # Convert relative path to absolute
    abs_path="$(cd "$(dirname "$input_path")" && pwd)/$(basename "$input_path")"
        
    # Check if realpath is available to resolve symlinks
    if command -v realpath >/dev/null 2>&1; then
        # Resolve symlink to actual path (if any)
        abs_path=$(realpath "$abs_path")
    else
        printf "Warning: 'realpath' command not found. Symlink resolution will be skipped.\n"
        printf "'realpath' can be installed via coreutils on macOS or GNU findutils on Linux.\n"
    fi

    # Return the resolved absolute path
    echo "$abs_path"
}

# Function to prompt user for a path to pre-installed submodules
submodule_path() {
    local var_name=$1
    local package_name=$2
    local default_value=${3:-}
    local user_input=""

    # If variable isn't set, initialize as empty
    if [ -z "${!var_name:-}" ]; then
        eval "$var_name=''"
    fi

    # Use indirect expansion only if the variable is set
    local current_value="${!var_name}"

    while true; do
        if [ -n "$current_value" ]; then
            printf "%s is currently set to: %s\n" "$var_name" "$current_value"
            printf "Do you want to keep this path? (y/n):"
            read choice || true
            case "$choice" in
                y|Y) return ;;
                n|N) break ;;
                *) printf "Invalid input. Please enter 'y' or 'n'.\n" ;;
            esac
        else
            break  # Exit loop if no current value
        fi
    done

    # Remove line(s) from env.sh
    remove_var_from_env "$var_name"

    while true; do
        printf "Enter the path for %s (leave blank to check out the submodule)" "$package_name"
        [ -n "$default_value" ] && printf " [default: %s]" "$default_value"
        printf ": "

        read user_input || true
        if [ -z "$user_input" ] && [ -n "$default_value" ]; then
            user_input="$default_value"
        fi

        # If no path is provided, remove the variable from env.sh
        if [ -z "$user_input" ]; then
            break  # No path entered, will not add it to env.sh
        fi

        # Convert relative path to absolute path
        abs_path=$(get_absolute_path "$user_input")

        # Check if the path exists
        if [ -d "$abs_path" ]; then
            # Check to make sure ScannerS/build exists
            if [ "$var_name" = "SCANNERS_PATH" ] && [ ! -d "$abs_path/build" ]; then
                printf "Error: The directory '%s/build' does not exist. Ensure ScannerS is properly compiled before proceeding.\n" "$abs_path"
                continue  # Prompt user again
            fi
            break  # Valid path, exit loop
        else
            printf "Error: The path '$user_input' ($abs_path) does not exist. Please enter a valid path.\n"
        fi
    done

    # Only write to env.sh if a valid path was provided
    if [ -n "$user_input" ]; then
        echo "export $var_name=\"$abs_path\"" >> env.sh
        export "$var_name"="$abs_path"  # Export the variable to the current subshell
    fi
}

# Function to create symlink for run/output
create_output_symlink() {
    local output_dir=""

    # If run/output exists, don't do anything
    if [ -e "run/output" ] || [ -L "run/output" ]; then
        return
    fi

    # Print information for user
    printf "\nIf you have an existing directory to store the output, please provide it. Otherwise a directory will be created.\n\n"

    # Prompt user for the desired output directory if not provided
    if [ -z "$output_dir" ]; then
        while true; do
            printf "Enter the desired path for the output directory (leave blank to create a new directory): "
            read output_dir || true
            if [ -n "$output_dir" ]; then
                # Convert relative path to absolute path
                abs_output_dir=$(get_absolute_path "$output_dir")

                # Check if the provided directory exists
                if [ -d "$abs_output_dir" ]; then
                    break
                else
                    printf "Error: The path '$abs_output_dir' does not exist. Please provide a valid path.\n"
                fi
            else
                # Create a new directory if no path is provided
                mkdir -p "run/output"
                printf "New directory 'run/output' created.\n"
                return
            fi
        done
    fi

    # Create symlink from run/output to the provided directory
    ln -s "$abs_output_dir" run/output
    printf "Symlink created: 'run/output' -> '$abs_output_dir'\n"
}

# Print information for user
printf "Setting up paths to pre-installed versions of the submodules, if they exist.\n"
printf "If no path is provided, the submodules will be checked out.\n\n"

# Prompt user for ScannerS and HiggsTools paths
submodule_path SCANNERS_PATH "ScannerS"
submodule_path HIGGSTOOLS_PATH "HiggsTools"
submodule_path HBDATASET_PATH "HBDataSet"
submodule_path HSDATASET_PATH "HSDataSet"

# Call function to handle symlink creation for run/output
create_output_symlink

# Remove directory variables from env.sh
remove_var_from_env "DATA_DIR"
remove_var_from_env "EXTERNALS_DIR"
remove_var_from_env "CONFIG_DIR"
remove_var_from_env "OUTPUT_DIR"
remove_var_from_env "HTCONDOR_DIR"

# Remove PATH variables from env.sh
remove_path_blocks_from_env

# Add various directories to env.sh
echo "export DATA_DIR=\"${PWD}/data\"" >> env.sh
echo "export EXTERNALS_DIR=\"${PWD}/externals\"" >> env.sh
echo "export CONFIG_DIR=\"${PWD}/config\"" >> env.sh
echo "export OUTPUT_DIR=\"${PWD}/run/output\"" >> env.sh
echo "export HTCONDOR_DIR=\"${PWD}/htcondor\"" >> env.sh

# Ensure SCANNERS_PATH is set correctly
if [ -n "${SCANNERS_PATH:-}" ] && [ -d "$SCANNERS_PATH/build" ]; then
    scanners_bin_path="$SCANNERS_PATH/build"
else
    scanners_bin_path="$PWD/externals/ScannerS/build"
fi

# Append the new PATH setting to env.sh
echo 'if [[ ":$PATH:" != *":'"${PWD}/python"':"* ]]; then' >> env.sh
echo '    export PATH="'"${PWD}/python"':$PATH"' >> env.sh
echo 'fi' >> env.sh
echo 'if [[ ":$PATH:" != *":'"$scanners_bin_path"':"* ]]; then' >> env.sh
echo '    export PATH="'"$scanners_bin_path"':$PATH"' >> env.sh
echo 'fi' >> env.sh

# Create file to indicate that all paths have been successfully set
touch .paths_ok
