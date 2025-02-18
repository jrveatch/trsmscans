#!/usr/bin/env sh

FORCE_RUN=false
CLEAN_RUN=false

# Parse command-line arguments safely
while [ $# -gt 0 ]; do
    case "$1" in
        -f) FORCE_RUN=true ;;
        -c) CLEAN_RUN=true ;;
        *) echo "Usage: $0 [-f] [-c]"; exit 1 ;;
    esac
    shift  # Shift to the next argument
done

# If clean mode is enabled, remove all flag files and environment settings
if [ "$CLEAN_RUN" = true ]; then
    printf "Cleaning setup state...\n"
    rm -f .deps_ok .submodules_ok env.sh
    rm -rf trsm_venv  # Remove virtual environment
fi

# Check dependencies
if [ "$FORCE_RUN" = true ] || [ ! -f ".deps_ok" ]; then
    printf "Checking dependencies:\n"
    if ! bash scripts/check_deps.sh; then
        echo "Error: check_deps.sh failed!" >&2
        return 1
    fi
else
    printf "Dependencies already checked\n"
fi

# Set user paths
if [ "$FORCE_RUN" = true ] || [ ! -f env.sh ]; then
    printf "\nSetting up user paths:\n"
    if ! bash scripts/set_user_paths.sh; then
        echo "Error: set_user_paths.sh failed!" >&2
        return 1
    fi
else
    printf "User paths already set. If you want to reset them, delete \"env.sh\" and run this script again\n"
fi

# source env.sh to load existing environment variables
if [ -f env.sh ]; then
    source env.sh
fi

# Set up submodules
if [ "$FORCE_RUN" = true ] || [ ! -f ".submodules_ok" ]; then
    printf "\nSetting up submodules:\n"
    if ! bash scripts/setup_submodules.sh; then
        echo "Error: setup_submodules.sh failed!" >&2
        return 1
    fi
else
    printf "Submodules already set up\n"
fi

# Set up python virtual environment if it doesn't exist
if [ "$FORCE_RUN" = true ] || [ ! -d trsm_venv ]; then
    printf "\nSetting up python virtual environment:\n"
    if ! bash scripts/setup_venv.sh; then
        echo "Error: setup_venv.sh failed!" >&2
        return 1
    fi
else
    printf "Virtual environment already set up\n"
fi

# Start python virtual environment
source scripts/start_venv.sh

# Update submodules
if ! bash scripts/update_submodules.sh; then
    echo "Error: update_submodules.sh failed!" >&2
    return 1
fi

# Install ScannerS
if [ "$FORCE_RUN" = true ] || { [ ! -d "externals/ScannerS/build" ] && [ -z "$SCANNERS_PATH" ]; }; then
    if ! bash scripts/compile_scanners.sh; then
        echo "Error: compile_scanners.sh failed!" >&2
        return 1
    fi
else
    printf "ScannerS already compiled\n"
fi

# Install HiggsTools
if [ "$FORCE_RUN" = true ] || { [ ! -d "externals/higgstools/_skbuild" ] && [ -z "$HIGGSTOOLS_PATH" ]; }; then
    if ! bash scripts/compile_higgstools.sh; then
        echo "Error: compile_higgstools.sh failed!" >&2
        return 1
    fi
else
    printf "HiggsTools already compiled\n"
fi
