
#!/bin/bash

# make prescan output directory if it doesn't exist
if [ ! -d "run/output/prescan" ]; then
    mkdir -p run/output/prescan
fi

# make scan output directory if it doesn't exist
if [ ! -d "run/output/scan" ]; then
    mkdir -p run/output/scan
fi
