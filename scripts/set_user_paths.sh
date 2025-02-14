#!/usr/bin/env sh

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
    local package_name=$2  # Used for generating the prompt message
    local default_value=${3:-}
    local user_input=""

    # Ensure env.sh exists
    if [ ! -f env.sh ]; then
        touch env.sh  # Create env.sh if it doesn't exist
    fi

    # Use sed to remove any existing export line for the variable
    if [ "$(uname)" = "Darwin" ]; then
        # On macOS, we use sed -i '' for in-place editing
        sed -i '' "/^export $var_name=/d" env.sh
    else
        # On Linux, we use sed -i
        sed -i "/^export $var_name=/d" env.sh
    fi

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
            break  # Valid path, exit loop
        else
            printf "Error: The path '$user_input' ($abs_path) does not exist. Please enter a valid path.\n"
        fi
    done

    # Export the variable
    export "$var_name"="$abs_path"

    # Only write to env.sh if a valid path was provided
    if [ -n "$user_input" ]; then
        echo "export $var_name=\"$abs_path\"" >> env.sh
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

# Prompt user for ScannerS and higgstools paths
submodule_path SCANNERS_PATH "ScannerS"
submodule_path HIGGSTOOLS_PATH "higgstools"
submodule_path HBDATASET_PATH "data/hbdataset"
submodule_path HSDATASET_PATH "data/hsdataset"

# Call function to handle symlink creation for run/output
create_output_symlink
