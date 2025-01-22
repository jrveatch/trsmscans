#!/usr/bin/env python3

import os
from functools import lru_cache

# TODO: Move from a simple .txt file to a .yaml/json file for better structure and parsing

@lru_cache(maxsize=None)
def valid_decays() -> set[str]:

    # decay mode file name
    file_name = os.path.join(os.environ['DATADIR'], "decaymodes.txt")

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

def get_non_resolvable_decay(decay: str) -> str:
    if "bbbb" in decay:
        return "Xbbbb"
    if "bb" in decay and "tautau" in decay:
        return "Xbbtautau"
    if "bb" in decay and "WW" in decay:
        return "XbbWW"
    if "bb" in decay and "ZZ" in decay:
        return "XbbZZ"
    if "bb" in decay and "VV" in decay:
        return "XbbVV"
    if "bb" in decay and "gamgam" in decay:
        return "Xbbgamgam"
    if "WW" in decay and "tautau" in decay:
        return "XWWtautau"
    if "ZZ" in decay and "tautau" in decay:
        return "XZZtautau"
    if "VV" in decay and "tautau" in decay:
        return "XVVtautau"
    return "None"
