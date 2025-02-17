
# standard libraries
import os
import shutil
from typing import List, Optional

# local modules
from utils.model import Model

def output_dir() -> str:
    """
    Get path to output directory.
    """
    return os.environ['OUTPUTDIR']

def scan_dir(model: 'Model',
             decay: str) -> str:
    """
    Get the directory path for the scan for a given model, decay, and masses.
    """
    return output_dir()+model.name+f"/scan/{decay}/{model.mass_string}/"

def prescan_dir(model: 'Model') -> str:
    """
    Get the directory path for the prescan for a given model and masses.
    """
    return output_dir()+model.name+f"/prescan/{model.mass_string}/"

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
    return output_dir()+model.name+f"/plots/{decay}/{model.mass_string}/"

def recreate_dir(path: str,
                 subdirs: Optional[List[str]] = None) -> None:
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

def config_dir() -> str:
    """
    Get path to config directory.
    """
    return os.environ['CONFIGDIR']

def data_dir() -> str:
    """
    Get path to data directory.
    """
    return os.environ['DATADIR']

def hbdataset_dir() -> str:
    """
    Get path to HBDataset directory.
    """
    if "HBDATASET_PATH" in os.environ:
        return os.environ['HBDATASET_PATH']
    else:
        return data_dir()+"hbdataset/"

def hsdataset_dir() -> str:
    """
    Get path to HSDataset directory.
    """
    if "HSDATASET_PATH" in os.environ:
        return os.environ['HSDATASET_PATH']
    else:
        return data_dir()+"hsdataset/"
