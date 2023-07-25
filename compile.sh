
# compile ScannerS
cd ScannerS
mkdir build && cd build
# currently hardcoded for JV's version of gcc
CC=gcc-13 CXX=g++-13 cmake ..
make
cd ../..

# compile higgstools with C++
#cd higgstools
#mkdir build && cd build
#cmake ..
#make
#cd ../..

# compile higgstools python module
#cd higgstools
#pip install .
#cd ..

