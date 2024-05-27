
#!/bin/bash

# List of submodule paths (relative to the root of the repository)
SUBMODULE_PATHS=("higgstools" "ScannerS")

# Print some information for user
echo "Checking for submodule updates"

# Update submodules
git submodule update --remote --recursive

# Loop through each submodule
for SUBMODULE_PATH in "${SUBMODULE_PATHS[@]}"; do
    echo "Checking submodule: $SUBMODULE_PATH"

    # Check if the submodule has been updated
    cd $SUBMODULE_PATH
    if [ -n "$(git diff --name-only HEAD@{1} HEAD)" ]; then
        echo "$SUBMODULE_PATH submodule has been updated."

        if [ -d build ]; then

            # Move into build directory and recompile
            cd build
            make
            cd ..

            # If higgstools is updated, pip install it as well
            if [[ $SUBMODULE_PATH == "higgstools" ]]; then
                pip install .
            fi

        fi

    else
        echo "Submodule $SUBMODULE_PATH has not been updated"
    fi
    cd ..
done

echo "All submodules are updated to the latest commit"
