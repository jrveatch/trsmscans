
from datetime import datetime
import json
import logging
import os
from typing import Optional

# get logger
logger = logging.getLogger(__name__)

def metadata_file_name(optimization: str) -> str:
    """Generate a metadata file name based on the optimization."""
    return os.path.join(optimization,f"run_metadata_{optimization}.json")

def save_run_metadata(out_dir: str,
                      optimization: str,
                      num_points: Optional[int] = None,
                      num_iterations: Optional[int] = None) -> None:
    """Save run metadata to a JSON file."""
    os.makedirs(os.path.join(out_dir,optimization), exist_ok=True)

    metadata = {"optimization": optimization}
    if num_points is not None:
        metadata["num_points"] = num_points
    if num_iterations is not None:
        metadata["num_iterations"] = num_iterations
    metadata["time_stamp"] = datetime.now().isoformat()

    metadata_path = os.path.join(out_dir, metadata_file_name(optimization))
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

def run_exists(out_dir: str,
               optimization: str,
               num_points: int = -1,
               num_iterations: int = -1) -> bool:
    """Check if a run exists by looking for the metadata file."""
    metadata_path = os.path.join(out_dir, metadata_file_name(optimization))
    if os.path.isfile(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            logger.info(f"Found a {optimization} run with {metadata['num_points']} points\n")
            if optimization == "zoom":
                return num_points <= 1.5*metadata["num_points"]
            if optimization == "meanshift":
                return num_iterations <= 1.5*metadata["num_iterations"]
    return False
