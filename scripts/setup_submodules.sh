#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Set environment variables from env.sh if it exists
if [ -f env.sh ]; then
    source env.sh
fi

# === Submodule Configuration ===

# ScannerS
SCANNERS_PATH_DEFAULT="externals/ScannerS"
SCANNERS_GIT_SSH="git@gitlab.com:jonaswittbrodt/ScannerS.git"
SCANNERS_GIT_HTTPS="https://gitlab.com/jonaswittbrodt/ScannerS.git"
SCANNERS_ENV_VAR="SCANNERS_PATH"

# HiggsTools
HIGGSTOOLS_PATH_DEFAULT="externals/higgstools"
HIGGSTOOLS_GIT_SSH="git@gitlab.com:higgsbounds/higgstools.git"
HIGGSTOOLS_GIT_HTTPS="https://gitlab.com/higgsbounds/higgstools.git"
HIGGSTOOLS_ENV_VAR="HIGGSTOOLS_PATH"

# HBDataSet
HBDATASET_PATH_DEFAULT="data/hbdataset"
HBDATASET_GIT_SSH="git@gitlab.com:higgsbounds/hbdataset.git"
HBDATASET_GIT_HTTPS="https://gitlab.com/higgsbounds/hbdataset.git"
HBDATASET_ENV_VAR="HBDATASET_PATH"

# HSDataSet
HSDATASET_PATH_DEFAULT="data/hsdataset"
HSDATASET_GIT_SSH="git@gitlab.com:higgsbounds/hsdataset.git"
HSDATASET_GIT_HTTPS="https://gitlab.com/higgsbounds/hsdataset.git"
HSDATASET_ENV_VAR="HSDATASET_PATH"

# === Helper: Test for SSH access to gitlab.com ===
function has_ssh_access() {
    ssh -T git@gitlab.com -o BatchMode=yes -o ConnectTimeout=5 2>&1 | grep -q "Welcome"
}

# === Helper: Handle submodule ===
function setup_submodule() {
  local name="$1"
  local path_default="$2"
  local git_ssh="$3"
  local git_https="$4"
  local env_var_name="$5"

  local user_path="${!env_var_name}"

  if [[ -n "$user_path" ]]; then
    echo "Using manually provided path for $name: $user_path"
    if [[ ! -d "$user_path/.git" ]]; then
      echo "Error: $user_path is not a valid Git repository."
      exit 1
    fi
    rm -rf "$path_default"
    ln -s "$user_path" "$path_default"
    return
  fi

  echo "Setting up $name at $path_default"

  local method
  if [[ -n "$GIT_METHOD" ]]; then
    method="$GIT_METHOD"
    echo "GIT_METHOD set to '$method'"
  else
    if has_ssh_access; then
      method="ssh"
      echo "Detected SSH access — using SSH for $name"
    else
      method="https"
      echo "SSH not available — falling back to HTTPS for $name"
    fi
  fi

  local repo_url
  if [[ "$method" == "ssh" ]]; then
    repo_url="$git_ssh"
  elif [[ "$method" == "https" ]]; then
    repo_url="$git_https"
  else
    echo "Unknown GIT_METHOD: $method"
    exit 1
  fi

  if [[ -d "$path_default/.git" ]]; then
    echo "$name already cloned, skipping clone."
  else
    git clone "$repo_url" "$path_default"
  fi
}

# === Main ===
setup_submodule "ScannerS"     "$SCANNERS_PATH_DEFAULT"     "$SCANNERS_GIT_SSH"     "$SCANNERS_GIT_HTTPS"     "$SCANNERS_ENV_VAR"
setup_submodule "HiggsTools"   "$HIGGSTOOLS_PATH_DEFAULT"   "$HIGGSTOOLS_GIT_SSH"   "$HIGGSTOOLS_GIT_HTTPS"   "$HIGGSTOOLS_ENV_VAR"
setup_submodule "HBDataSet"    "$HBDATASET_PATH_DEFAULT"    "$HBDATASET_GIT_SSH"    "$HBDATASET_GIT_HTTPS"    "$HBDATASET_ENV_VAR"
setup_submodule "HSDataSet"    "$HSDATASET_PATH_DEFAULT"    "$HSDATASET_GIT_SSH"    "$HSDATASET_GIT_HTTPS"    "$HSDATASET_ENV_VAR"

echo "All submodules set up."

# Create a file to indicate that submodules are set up
touch .submodules_ok

exit

# Check if SCANNERS_PATH is set, if so, skip ScannerS submodule
if [ -z "${SCANNERS_PATH:-}" ]; then
    printf "Initializing and updating ScannerS submodule...\n"
    git submodule update --init --recursive externals/ScannerS
else
    printf "Skipping ScannerS submodule as SCANNERS_PATH is set to $SCANNERS_PATH\n"
fi

# Check if HIGGSTOOLS_PATH is set, if so, skip HiggsTools submodule
if [ -z "${HIGGSTOOLS_PATH:-}" ]; then
    printf "Initializing and updating HiggsTools submodule...\n"
    git submodule update --init --recursive externals/higgstools
else
    printf "Skipping HiggsTools submodule as HIGGSTOOLS_PATH is set to $HIGGSTOOLS_PATH\n"
fi

# Check if HBDATASET_PATH is set, if so, skip HBDataSet submodule
if [ -z "${HBDATASET_PATH:-}" ]; then
    printf "Initializing and updating HBDataSet submodule...\n"
    git submodule update --init --recursive data/hbdataset
else
    printf "Skipping HBDataSet submodule as HBDATASET_PATH is set to $HBDATASET_PATH\n"
fi

# Check if HSDATASET_PATH is set, if so, skip HSDataSet submodule
if [ -z "${HSDATASET_PATH:-}" ]; then
    printf "Initializing and updating HSDataSet submodule...\n"
    git submodule update --init --recursive data/hsdataset
else
    printf "Skipping HSDataSet submodule as HSDATASET_PATH is set to $HSDATASET_PATH\n"
fi

# Create a file to indicate that submodules are set up
touch .submodules_ok
