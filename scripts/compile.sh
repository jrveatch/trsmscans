
# compile ScannerS
printf "\n"
printf "Trying to compile ScannerS"
printf "\n"
cd ScannerS
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools with C++
printf "\n"
printf "Trying to compile higgstools"
printf "\n"
cd higgstools
if [ ! -d build ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_CXX_STANDARD=17 -Wno-dev ..
make
cd ../..

# compile higgstools python module
printf "\n"
printf "Trying to compile higgstools python"
printf "\n"
cd higgstools
pip install .
cd ..
