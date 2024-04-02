
#!/bin/bash

# make output directory if it doesn't exist
if [ ! -d "run/output" ]; then
    mkdir run/output
fi

# make prescan output directory if it doesn't exist
if [ ! -d "run/output/prescan" ]; then
    mkdir run/output/prescan
fi

# make scan output directory if it doesn't exist
if [ ! -d "run/output/scan" ]; then
    mkdir run/output/scan
fi
