#!/usr/bin/env sh

# Function to prompt user for a path
prompt_for_path() {
    local var_name=$1
    local package_name=$2  # Used for generating the prompt message
    local default_value=${3:-}
    local user_input=""

    while true; do
        printf "Enter the path for %s" "$package_name"
        [ -n "$default_value" ] && printf " [default: %s]" "$default_value"
        printf ": "

        read user_input || true
        if [ -z "$user_input" ] && [ -n "$default_value" ]; then
            user_input="$default_value"
        fi

        # Convert relative path to absolute path
        user_input="$(cd "$(dirname "$user_input")" && pwd)/$(basename "$user_input")"
        
        # Resolve symlink to actual path (if any)
        user_input=$(realpath "$user_input")

        # Check if the path exists
        if [ -d "$user_input" ]; then
            break  # Valid path, exit loop
        else
            echo "Error: The path '$user_input' does not exist. Please enter a valid path."
        fi
    done

    # Use sed_command to remove any existing export line for the variable
    if [ "$(uname)" = "Darwin" ]; then
        # On macOS, we use sed -i '' for in-place editing
        sed -i '' "/^export $var_name=/d" env.sh
    else
        # On Linux, we use sed -i
        sed -i "/^export $var_name=/d" env.sh
    fi

    # Export path and overwrite the previous entry in env.sh
    export "$var_name"="$user_input"
    echo "export $var_name=\"$user_input\"" >> env.sh
}

# Prompt user for ScannerS and higgstools paths
prompt_for_path SCANNERS_PATH "ScannerS"
prompt_for_path HIGGSTOOLS_PATH "higgstools"
