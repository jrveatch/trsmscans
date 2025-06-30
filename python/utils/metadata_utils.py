
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, Optional

from utils.precision_utils import Precision

# get logger
logger = logging.getLogger(__name__)

def metadata_file_name(strategy: str) -> str:
    """Generate a metadata file name based on the optimization strategy."""
    return os.path.join(strategy,f"run_metadata_{strategy}.json")

def save_run_metadata(out_dir: str,
                      strategy: str,
                      num_points: Optional[int] = None,
                      precision: Optional[Precision] = None) -> None:
    """Save run metadata to a JSON file."""
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
               num_points: int = -1) -> bool:
    """Check if a run exists by looking for the metadata file."""
    metadata_path = os.path.join(out_dir, metadata_file_name(strategy))
    if not os.path.isfile(metadata_path):
        return False

    with open(metadata_path, "r") as f:
        metadata: Dict[str, Any] = json.load(f)

    existing_points: int = metadata.get("num_points", 0)
    logger.info(f"Found a {strategy} run with {existing_points} points")

    if strategy == "zoom":
        if num_points <= 1.5 * existing_points:
            return True
    if strategy == "meanshift":
        return num_points <= 1.2 * existing_points

    return False
