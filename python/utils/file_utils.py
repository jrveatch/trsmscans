
# standard libraries
import os
import shutil
from typing import List, Optional

# local modules
from utils.env_utils import output_dir
from utils.model import Model

def scan_dir(model: Model,
             decay: str) -> str:
    """
    Get the directory path for the scan for a given model and decay.

    Args:
        model (Model): The model object containing mass information.
        decay (str): The decay type.

    Returns:
        str: The path to the scan directory.
    """

    return os.path.join(output_dir(),model.name,"scan",decay,model.mass_string)

def prescan_dir(model: Model) -> str:
    """
    Get the directory path for the prescan for a given model.

    Args:
        model (Model): The model object containing mass information.

    Returns:
        str: The path to the prescan directory.
    """
    return os.path.join(output_dir(),model.name,"prescan",model.mass_string)

def prescan_tsv(model: Model) -> str:
    """
    Get the path to the prescan .tsv file for a given model.

    Args:
        model (Model): The model object containing mass information.

    Returns:
        str: The path to the prescan .tsv file.
    """
    return os.path.join(prescan_dir(model),f"{model.name}_prescan.tsv")

def plots_dir(model: Model,
              decay: str) -> str:
    """
    Get the directory path for the plots for a given model and decay.

    Args:
        model (Model): The model object containing mass information.
        decay (str): The decay type.

    Returns:
        str: The path to the plots directory.
    """
    return os.path.join(output_dir(),model.name,"plots",decay,model.mass_string)

def recreate_dir(path: str,
                 subdirs: Optional[List[str]] = None) -> None:
    """
    Recreate the specified directory, optionally creating subdirectories.

    Args:
        path (str): The main directory path to recreate.
        subdirs (List[str], optional): A list of subdirectory names to create within the main directory.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    # create subdirectories if specified
    if subdirs:
        for subdir in subdirs:
            os.makedirs(os.path.join(path, subdir))
