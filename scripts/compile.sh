
# compile ScannerS
echo "\n"
echo "Trying to compile ScannerS"
echo "\n"
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools with C++
echo "\n"
echo "Trying to compile higgstools"
echo "\n"
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools python module
echo "\n"
echo "Trying to compile higgstools python"
echo "\n"
cd higgstools
pip install .
cd ..

