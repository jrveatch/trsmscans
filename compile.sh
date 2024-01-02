
# compile ScannerS
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
# currently hardcoded for JV's version of gcc
CC=gcc-13 CXX=g++-13 cmake -Wno-dev ..
make
cd ../..

# compile higgstools with C++
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -Wno-dev ..
make
cd ../..

# compile higgstools python module
cd higgstools
pip install .
cd ..

