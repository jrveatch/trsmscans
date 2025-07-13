
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, Optional

from utils.precision_utils import Precision

# get logger
logger = logging.getLogger(__name__)

def metadata_file_name(strategy: str) -> str:
    """
    Generate a metadata file name for a given optimization strategy.

    Args:
        strategy (str): Name of the optimization strategy (e.g., "zoom", "meanshift").

    Returns:
        str: Relative path to the metadata JSON file.
    """
    return os.path.join(strategy,f"run_metadata_{strategy}.json")

def load_metadata(path: str) -> Dict[str, Any]:
    """
    Load and parse run metadata from a JSON file.

    Args:
        path (str): Full path to the metadata JSON file.

    Returns:
        Dict[str, Any]: Parsed metadata dictionary.

    Raises:
        OSError: If the file cannot be read.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(path, "r") as f:
        return json.load(f)

def save_run_metadata(out_dir: str,
                      strategy: str,
                      num_points: Optional[int] = None,
                      precision: Optional[Precision] = None) -> None:
    """
    Save run metadata (e.g., number of points, precision) to a JSON file.

    Args:
        out_dir (str): Output directory where strategy subdir will be created.
        strategy (str): Optimization strategy name.
        num_points (Optional[int]): Number of sampled points (if known).
        precision (Optional[Precision]): Achieved precision level (if known).

    Returns:
        None

    Raises:
        OSError: If writing to the metadata file fails.
    """
    os.makedirs(os.path.join(out_dir,strategy), exist_ok=True)

    metadata: Dict[str, Any] = {"strategy": strategy}
    if num_points is not None:
        metadata["num_points"] = num_points
    if precision is not None:
        metadata["precision"] = str(precision)
    metadata["time_stamp"] = datetime.now().isoformat()

    metadata_path = os.path.join(out_dir, metadata_file_name(strategy))
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

def run_exists(out_dir: str,
               strategy: str,
               num_points: int = -1,
               precision: Optional[Precision] = None) -> bool:
    """
    Check if a previous run exists with sufficient sampling and, for zoom, sufficient precision.

    For 'zoom' strategy:
        - Returns True if a metadata file exists and contains at least (num_points / 1.5)
          and meets the requested precision (if provided).
    For 'meanshift' strategy:
        - Returns True if the metadata file contains at least (num_points / 1.2).
        - Precision is not checked.

    Args:
        out_dir (str): Directory where metadata should be found.
        strategy (str): Strategy name ("zoom" or "meanshift").
        num_points (int): Number of points expected in the new run.
        precision (Optional[Precision]): Minimum required precision (only checked for 'zoom').

    Returns:
        bool: True if an existing run satisfies the requirements, False otherwise.

    Raises:
        OSError: If the metadata file exists but cannot be read.
        json.JSONDecodeError: If the metadata file is not valid JSON.
    """
    metadata_path = os.path.join(out_dir, metadata_file_name(strategy))
    if not os.path.isfile(metadata_path):
        return False

    metadata = load_metadata(metadata_path)
    existing_points: int = metadata.get("num_points", 0)
    existing_precision = get_precision(metadata)

    logger.info(f"Found a {strategy} run with {existing_points} points"
                f"{' and precision ' + str(existing_precision) if existing_precision is not None else ''}.")

    if strategy == "zoom":
        # Check point threshold
        if num_points > 1.5 * existing_points:
            return False
        # Handle optional precision logic
        if precision is not None:
            if existing_precision is None:
                logger.info("Existing run has no precision field; cannot satisfy fixed precision requirement.")
                return False
            if existing_precision < precision:
                logger.info(f"Existing precision '{existing_precision}' is lower than requested '{precision}'.")
                return False
        return True

    if strategy == "meanshift":
        return num_points <= 1.2 * existing_points

    return False

def get_precision(data: Dict[str, Any]) -> Optional[Precision]:
    """
    Extract the precision level from metadata, if present and valid.

    Args:
        data (Dict[str, Any]): Parsed metadata dictionary.

    Returns:
        Optional[Precision]: Precision value if present and valid, otherwise None.
    """
    precision_str = data.get("precision")
    if precision_str is None:
        return None
    try:
        return Precision.from_string(precision_str)
    except ValueError:
        return None
