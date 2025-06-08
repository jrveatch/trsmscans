#!/usr/bin/env bash

# Function to remove variable from env.sh
remove_var_from_env() {
    local var_name=$1
    if [ "$(uname)" = "Darwin" ]; then
       # On macOS, we use sed -i '' for in-place editing
        sed -i '' "/^export $var_name=/d" env.sh
    else
        # On Linux, we use sed -i
        sed -i "/^export $var_name=/d" env.sh
    fi
}

# Function to remove blocks that modify PATH from env.sh
remove_path_blocks_from_env() {
    awk '
    BEGIN { skip = 0 }
    /^\s*if\s+\[\[\s+":\$PATH:"\s+!=/ {
        block = $0 "\n"
        skip = 1
        next
    }
    skip {
        block = block $0 "\n"
        if ($0 ~ /fi/) {
            if (block ~ /export PATH=.*\$PATH/) {
                skip = 0
                block = ""
                next
            } else {
                printf "%s", block
                skip = 0
                block = ""
                next
            }
        }
        next
    }
    { print }
    ' env.sh > env.sh.tmp && mv env.sh.tmp env.sh
}

# Function to check if an installed version is less than the required version
version_less_than() {
  local installed_version=$1
  local required_version=$2

  local installed_major installed_minor required_major required_minor
  IFS='.' read -r installed_major installed_minor _ <<< "$installed_version"
  IFS='.' read -r required_major required_minor _ <<< "$required_version"

  if [[ $installed_major -lt $required_major ]]; then
    return 0
  elif [[ $installed_major -eq $required_major && $installed_minor -lt $required_minor ]]; then
    return 0
  else
    return 1
  fi
}
