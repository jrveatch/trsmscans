
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, Optional

from utils.file_utils import output_dir
from utils.model import Model
from utils.precision_utils import Precision
from utils.tsv_utils import count_tsv_points

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

def get_mass_point_status(model: Model,
                          decay: str,
                          threshold: int,
                          mode: str,
                          strategy: Optional[str] = None,
                          precision: Optional[Precision] = None
                          ) -> Tuple[str, Optional[int], Optional[Precision]]:
    """
    Check the scan or prescan status of a single (X, S) mass point.

    Args:
        model (Model): Model to use.
        decay (str): Decay mode to use exactly as provided.
        threshold (int): Minimum required number of points.
        mode (str): Either "prescan" or "scan".
        strategy (Optional[str]): Optimization strategy. Required if mode is "scan".
        precision (Optional[Precision]): Minimum required precision.

    Returns:
        Tuple[str, Optional[int], Optional[Precision]]:
            - Status: One of {"ok", "below_threshold", "low_precision", "missing", "non_calculable"}
            - Count of points if applicable (None for "missing" or "non_calculable")
            - Previous precision (None if field is not saved)

    Raises:
        ValueError: If required parameters are missing or invalid.
        OSError / JSONDecodeError: If files are corrupt or unreadable.
    """
    subdir = model.mass_string

    if not model.is_calculable:
        return "non_calculable", None, None

    if mode == "prescan":
        path = os.path.join(output_dir(), model.name, "prescan", subdir, f"{model.name}_prescan.tsv")
        if not os.path.isfile(path):
            return "missing", None, None
        count = count_tsv_points(path)
        return ("ok", count, None) if count >= threshold else ("below_threshold", count, None)

    elif mode == "scan":
        if strategy is None:
            raise ValueError("Scan mode requires a strategy.")
        path = os.path.join(output_dir(), model.name, "scan", decay, subdir,
                            strategy, f"run_metadata_{strategy}.json")
        if not os.path.isfile(path):
            return "missing", None, None
        metadata = load_metadata(path)

        count = metadata.get("num_points", 0)
        prev_precision = get_precision(metadata)

        if precision is not None and (prev_precision is None or prev_precision < precision):
            return "low_precision", count, prev_precision
        return ("ok", count, prev_precision) if count >= threshold else ("below_threshold", count, prev_precision)

    else:
        raise ValueError(f"Invalid mode '{mode}'")
