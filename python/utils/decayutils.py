#!/usr/bin/env python3

import os

def is_valid_decay(decaymode: str) -> bool:

    # decay mode file name
    file_name = os.environ['DATADIR'] + "decaymodes.txt"

    # search for decaymode in file
    with open(file_name, 'r') as file:
        # loop over every line in the file
        for line in file:
            # skip blank lines
            if line.strip():
                # get first word from each line
                first_word = line.split()[0]
                if first_word == decaymode:
                    # if it is found, return True
                    return True

    # if it isn't found, return False
    return False
