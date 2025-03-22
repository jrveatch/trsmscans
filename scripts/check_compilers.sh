#!/usr/bin/env bash

set -e
set -u
set -o pipefail

###########################################
# C++
###########################################

# Check if a C++17-compatible compiler is available
check_cxx17_support() {

  # Create a temporary C++ file using mktemp
  TMP_CXX=$(mktemp /tmp/test_cxx17.XXXXXX.cpp)
  TMP_EXE=$(mktemp /tmp/test_cxx17.XXXXXX)  # Temporary executable file

  cat > "$TMP_CXX" <<EOF
#include <iostream>
int main() {
    std::cout << "C++17 is supported!" << std::endl;
    return 0;
}
EOF

  # Try compiling the test file with a C++ compiler and the C++17 flag
  for compiler in g++ clang++ c++ icpc pgc++; do
    if command -v "$compiler" >/dev/null 2>&1; then
      # Try compiling the file with the C++17 flag
      if $compiler -std=c++17 "$TMP_CXX" -o "$TMP_EXE" 2>/dev/null; then
        printf "Installed version of $compiler supports C++17!\n"
        rm -f "$TMP_CXX" "$TMP_EXE"
        return 0
      fi
    fi
  done

  # If no compiler worked, return error
  printf "No C++17-compatible compiler found.\n"
  rm -f "$TMP_CXX"
  return 1
}

###########################################
# Fortran
###########################################

# Check if a Fortran compiler is available and can compile
check_fortran_support() {

  # Create temporary Fortran source and executable files
  TMP_F90=$(mktemp /tmp/test_fortran.XXXXXX.f90)
  TMP_EXE=$(mktemp /tmp/test_fortran.XXXXXX)

  cat > "$TMP_F90" <<EOF
program test_fortran
  print *, 'Fortran is supported!'
end program test_fortran
EOF

  # Try compiling the Fortran file with gfortran, ifort, or flang
  for compiler in gfortran ifort flang lfortran nvfortran; do
    if command -v "$compiler" >/dev/null 2>&1; then
      # Try compiling the file
      if $compiler "$TMP_F90" -o "$TMP_EXE" 2>/dev/null; then
        printf "Installed version of $compiler can compile Fortran!\n"
        rm -f "$TMP_F90" "$TMP_EXE"
        return 0
      else
        printf "$compiler failed to compile Fortran code.\n"
      fi
    fi
  done

  # If no Fortran compiler worked, exit with error
  printf "No Fortran compiler found or failed to compile.\n"
  rm -f "$TMP_F90"
  return 1
}

###########################################
# Clang
###########################################

# Check the installed clang version
check_clang_version() {
  # Check if clang is installed
  if ! command -v clang &>/dev/null; then
    printf "Error: clang is not installed.\n"
    return 1
  fi

  # Get the first line of clang version output
  CLANG_VERSION_OUTPUT=$(clang --version | head -n1)

  # Check if this is Apple Clang
  if echo "$CLANG_VERSION_OUTPUT" | grep -q "Apple clang"; then
    # Extract Apple Clang major version
    APPLE_CLANG_VERSION=$(echo "$CLANG_VERSION_OUTPUT" | grep -oE '[0-9]+\.[0-9]+' | head -1 | cut -d. -f1)

    # Apple Clang 7+ corresponds to LLVM Clang 5+
    if [[ "$APPLE_CLANG_VERSION" -ge 7 ]]; then
      printf "Apple clang version $APPLE_CLANG_VERSION detected, which is sufficient.\n"
      return 0
    else
      printf "Error: Apple clang version $APPLE_CLANG_VERSION is too old. Version 7 or higher is required.\n"
      return 1
    fi
  else
    # Extract upstream Clang major version
    CLANG_VERSION=$(echo "$CLANG_VERSION_OUTPUT" | grep -oE '[0-9]+' | head -1)

    # Check if version is >= 5
    if [[ "$CLANG_VERSION" -ge 5 ]]; then
      printf "clang version $CLANG_VERSION is installed and meets the requirement.\n"
      return 0
    else
      printf "Error: clang version $CLANG_VERSION is too old. Version 5 or higher is required.\n"
      return 1
    fi
  fi
}

# Call the functions
if ! check_cxx17_support; then
  exit 1
fi
if ! check_fortran_support; then
  exit 1
fi
if ! check_clang_version; then
  exit 1
fi
