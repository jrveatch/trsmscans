
# compile ScannerS
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools with C++
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools python module
cd higgstools
pip install .
cd ..

