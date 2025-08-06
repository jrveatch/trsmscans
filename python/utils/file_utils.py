
# standard libraries
import os
import shutil
import time
from typing import List, Optional

# get logger
import logging
logger = logging.getLogger(__name__)

# local modules
from utils.env_utils import output_dir
from utils.model import Model
from utils.logging_utils import VERBOSE_LEVEL

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
    return os.path.join(output_dir(),model.name,"plots",decay,"mass_points",model.mass_string)

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

def remove_artifact_files(model_name: str) -> None:
    """Remove artifact files that are not needed after the scan."""
    artifact_files = ["HS_analyses.txt",
                      "HS_correlations.txt",
                      "Key.dat", "STXS_analyses.txt",
                      "STXS_correlations.txt",
                      f"{model_name}.tsv"]
    for file in artifact_files:
        if os.path.exists(file):
            os.remove(file)
            logger.debug(f"Removed artifact file: {file}")
        else:
            logger.debug(f"Artifact file {file} does not exist, skipping removal.")

def remove_temp_directories(directories: List[str]) -> None:


    # Skip if directories is an empty list
    if not directories:
        return

    # If everything worked, proceed to delete directories
    logger.debug("Removing temp directories")
    for directory in directories:
        remove_temp_dir(directory)
    logger.debug("Successfully removed temp directories")

def remove_temp_dir(directory, retries=5, delay=1):
    for attempt in range(retries):
        try:
            shutil.rmtree(directory)
            if logger.isEnabledFor(VERBOSE_LEVEL):
                logger.verbose(f"Successfully removed: {directory}")  # type: ignore[attr-defined]
        except OSError as e:
            if 'Directory not empty' in str(e):
                if logger.isEnabledFor(VERBOSE_LEVEL):
                    logger.verbose(f"Attempt {attempt + 1}: Directory not empty, retrying in {delay} seconds...")  # type: ignore[attr-defined]
                time.sleep(delay)  # Wait before retrying
            else:
                raise  # Raise if it's another type of error
        else:
            return 
    logger.exception(f"Failed to remove {directory} after {retries} retries.")
