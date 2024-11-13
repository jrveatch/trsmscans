
#!/bin/bash

# Print some information for user
printf "Checking for submodule updates\n"

# Function to get the current commit hash and path of each submodule
get_submodule_hashes() {
  git submodule foreach --quiet 'echo $sm_path $(git rev-parse HEAD)'
}

# Save the current state of submodule hashes
before_update=$(mktemp)
get_submodule_hashes > "$before_update"

# Update submodules
git submodule update --remote --recursive

# Save the state of submodule hashes after the update
after_update=$(mktemp)
get_submodule_hashes > "$after_update"

# Compare the hashes before and after the update
updated_submodules=()
while IFS= read -r before; do
    # Get path to submodule
    submodule_path=$(echo "$before" | awk '{ print $1 }')

    # Get hashes before and after the update
    before_hash=$(echo "$before" | awk '{ print $2 }')
    after_hash=$(grep "$submodule_path" "$after_update" | awk '{ print $2 }')

    # If hash has changed, then compile
    if [ "$before_hash" != "$after_hash" ]; then

        # Print info to screen
        printf "Updating $submodule_path\n"

        # Store list of updated submodules
        updated_submodules+=("$submodule_path")

        # If higgstools or ScannerS is updated, recompile it
        if [[ "$submodule_path" == "higgstools" || "$submodule_path" == "ScannerS" ]]; then
            # Go into the submodule directory
            pushd $submodule_path > /dev/null || return 1

            # If build directory exists, remove it
            if [ -d build ]; then
                rm -rf build
            fi

            # Make build directory and recompile
            mkdir build
            pushd build > /dev/null || return 1
            cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
            make
            popd > /dev/null || return 1

            # If higgstools is updated, pip install it as well
            if [[ "$submodule_path" == "higgstools" ]]; then
                rm -rf _skbuild
                pip install .
            fi

            # Return to base directory
            popd > /dev/null || return 1
        fi

    fi
done < "$before_update"

# Print the results
if [ ${#updated_submodules[@]} -eq 0 ]; then
  printf "No submodules were updated\n"
else
  printf "The following submodules were updated:\n"
  for submodule in "${updated_submodules[@]}"; do
    printf "- $submodule\n"
  done
fi

# Cleanup temporary files
rm -rf "$before_update" "$after_update"

printf "All submodules are updated to the latest commit\n"
