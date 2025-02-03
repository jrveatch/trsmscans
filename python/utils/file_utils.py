
# standard libraries
import os
import shutil
from typing import Optional

# local modules
from utils.model import Model
def scan_dir(model: 'Model',
             decay: str) -> str:
    """
    Get the directory path for the scan for a given model, decay, and masses.
    """
    return os.environ['OUTPUTDIR']+model.name+f"/scan/{decay}/{model.mass_string}/"

def prescan_dir(model: 'Model') -> str:
    """
    Get the directory path for the prescan for a given model and masses.
    """
    return os.environ['OUTPUTDIR']+model.name+f"/prescan/{model.mass_string}/"

def prescan_tsv(model: 'Model') -> str:
    """
    Get the path to the prescan .tsv file for a given model and masses.
    """
    return prescan_dir(model)+model.name+"_prescan.tsv"

def plots_dir(model: 'Model',
              decay: str) -> str:
    """
    Get the directory path for the plots for a given model, decay, and masses.
    """
    return os.environ['OUTPUTDIR']+model.name+f"/plots/{decay}/{model.mass_string}/"

def recreate_dir(path: str,
                 subdirs: Optional[list[str]] = None) -> None:
    """
    Recreate the specified directory, optionally creating subdirectories.

    Parameters:
    - path (str): The main directory path to recreate.
    - subdirs (list of str, optional): A list of subdirectory names to create within the main directory.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    # create subdirectories if specified
    if subdirs:
        for subdir in subdirs:
            os.makedirs(os.path.join(path, subdir))
