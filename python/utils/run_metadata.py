import json
import logging
import os
import time

# get logger
logger = logging.getLogger(__name__)

metadata_file_name = "run_metadata.json"

def save_run_metadata(out_dir: str,
                      optimization: str,
                      num_points: int = -1) -> None:
    """Save run metadata to a JSON file."""
    metadata = {
        "optimization": optimization,
        "num_points": num_points,
        "timestamp": time.time()
    }
    metadata_path = os.path.join(out_dir, metadata_file_name)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)

def run_exists(out_dir: str,
               num_points: int = -1) -> bool:
    """Check if a run exists by looking for the metadata file."""
    metadata_path = os.path.join(out_dir, metadata_file_name)
    if os.path.isfile(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            match metadata["optimization"]:
                case "zoom":
                    logger.info(f"Found a zoom run with {metadata["num_points"]} points")
                    return num_points <= 1.5*metadata["num_points"]
    return False
