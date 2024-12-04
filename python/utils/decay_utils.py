#!/usr/bin/env python3

import os

def valid_decays() -> set[str]:

    # decay mode file name
    file_name = os.environ['DATADIR'] + "decaymodes.txt"

    # initialize empty set for the available decay modes
    strings_set = set()

    # open the file
    with open(file_name, "r") as file:
        for line in file:
            # strip leading/trailing whitespace
            stripped_line = line.strip()
            # skip comments and blank lines
            if not stripped_line or stripped_line.startswith("#"):
                continue
            # add the valid string to the set
            strings_set.add(stripped_line)
    return strings_set

def is_valid_decay(decay_mode: str) -> bool:

    return decay_mode in valid_decays()
