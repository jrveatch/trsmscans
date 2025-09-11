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
HBDATASET_PATH_DEFAULT="externals/hbdataset"
HBDATASET_GIT_SSH="git@gitlab.com:higgsbounds/hbdataset.git"
HBDATASET_GIT_HTTPS="https://gitlab.com/higgsbounds/hbdataset.git"
HBDATASET_ENV_VAR="HBDATASET_PATH"

# HSDataSet
HSDATASET_PATH_DEFAULT="externals/hsdataset"
HSDATASET_GIT_SSH="git@gitlab.com:higgsbounds/hsdataset.git"
HSDATASET_GIT_HTTPS="https://gitlab.com/higgsbounds/hsdataset.git"
HSDATASET_ENV_VAR="HSDATASET_PATH"

# === Helper: Test for SSH access to gitlab.com ===
function has_ssh_access() {
    ssh -T git@gitlab.com -o BatchMode=yes -o ConnectTimeout=5 2>&1 | grep -e "Welcome"
}

# === Helper: Handle submodule ===
function setup_submodule() {
  local name="$1"
  local path_default="$2"
  local git_ssh="$3"
  local git_https="$4"
  local env_var_name="$5"

  local user_path
  if printenv "$env_var_name" &>/dev/null; then
    user_path="${!env_var_name}"
  else
    user_path=""
  fi

  if [[ -n "$user_path" ]]; then
    printf "\nUsing manually provided path for $name: $user_path\n"
    rm -rf "$path_default"
    ln -s "$user_path" "$path_default"
    return
  fi

  printf "\nSetting up $name at $path_default\n"

  rm -rf "$path_default"

  local method
  if has_ssh_access; then
    method="ssh"
    printf "Detected SSH access — using SSH for $name\n"
  else
    method="https"
    printf "SSH not available — falling back to HTTPS for $name\n"
  fi

  local repo_url
  if [[ "$method" == "ssh" ]]; then
    repo_url="$git_ssh"
  elif [[ "$method" == "https" ]]; then
    repo_url="$git_https"
  else
    printf "Unknown git method: $method\n"
    exit 1
  fi

  if [[ -d "$path_default/.git" ]]; then
    printf "$name already cloned, skipping clone.\n"
  else
    git clone "$repo_url" "$path_default"
  fi
}

# === Main ===
setup_submodule "ScannerS"     "$SCANNERS_PATH_DEFAULT"     "$SCANNERS_GIT_SSH"     "$SCANNERS_GIT_HTTPS"     "$SCANNERS_ENV_VAR"
setup_submodule "HiggsTools"   "$HIGGSTOOLS_PATH_DEFAULT"   "$HIGGSTOOLS_GIT_SSH"   "$HIGGSTOOLS_GIT_HTTPS"   "$HIGGSTOOLS_ENV_VAR"
setup_submodule "HBDataSet"    "$HBDATASET_PATH_DEFAULT"    "$HBDATASET_GIT_SSH"    "$HBDATASET_GIT_HTTPS"    "$HBDATASET_ENV_VAR"
setup_submodule "HSDataSet"    "$HSDATASET_PATH_DEFAULT"    "$HSDATASET_GIT_SSH"    "$HSDATASET_GIT_HTTPS"    "$HSDATASET_ENV_VAR"

printf "\nAll submodules set up.\n"

# Create a file to indicate that submodules are set up
touch .submodules_ok
