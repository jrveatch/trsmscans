#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Check if a C++17-compatible compiler is available
check_cxx17_support() {
  # Create a temporary C++ file to test compilation with -std=c++17
  cat > /tmp/test_cxx17.cpp <<EOF
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
      if $compiler -std=c++17 /tmp/test_cxx17.cpp -o /tmp/test_cxx17 2>/dev/null; then
        echo Installed version of "$compiler supports C++17!"
        rm -f /tmp/test_cxx17.cpp /tmp/test_cxx17
        return 0
      fi
    fi
  done

  # If no compiler worked, return error
  echo "No C++17-compatible compiler found."
  rm -f /tmp/test_cxx17.cpp
  return 1
}

# Check if a Fortran compiler is available and can compile
check_fortran_support() {
  # Create a temporary Fortran file to test compilation
  cat > /tmp/test_fortran.f90 <<EOF
program test_fortran
  print *, 'Fortran is supported!'
end program test_fortran
EOF

  # Try compiling the Fortran file with gfortran, ifort, or flang
  for compiler in gfortran ifort flang; do
    if command -v "$compiler" >/dev/null 2>&1; then
      echo "Checking with $compiler..."

      # Try compiling the file
      if $compiler /tmp/test_fortran.f90 -o /tmp/test_fortran 2>/dev/null; then
        echo Installed version of "$compiler can compile Fortran!"
        rm -f /tmp/test_fortran.f90 /tmp/test_fortran
        exit 0
      else
        echo "$compiler failed to compile Fortran code."
      fi
    fi
  done

  # If no Fortran compiler worked, exit with error
  echo "No Fortran compiler found or failed to compile."
  rm -f /tmp/test_fortran.f90
  exit 1
}

# Call the functions
check_cxx17_support
check_fortran_support
