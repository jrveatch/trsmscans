
from functools import lru_cache
import logging
import multiprocessing as mp
import os

# local modules
from utils.config_loader import ConfigLoader

# get logger
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_n_cpus() -> int:
    """Return the number of CPUs available for this job.

    Checks for HTCondor-specific environment variables or fallback values,
    and adapts to both HTCondor batch and local execution.
    
    Returns:
        int: Number of CPUs this job should use.
    """
    # Case 1: Running under HTCondor
    for var in ("_CONDOR_NPROCS", "PYTHON_CPU_COUNT", "REQUEST_CPUS", "NUM_CPUS"):
        val = os.environ.get(var)
        if val:
            try:
                parsed = int(val)
                logger.debug(f"Detected {parsed} CPUs from {var}.")
                return parsed
            except ValueError:
                logger.warning(f"Environment variable {var} is not an integer: {val}")

    # Case 2: Running locally
    total = mp.cpu_count()
    reserve = _get_local_cpu_reserve(total)
    n_cpus = max(1, total - reserve)
    logger.debug(f"Total CPUs available: {total}, CPUs reserved: {reserve}, CPUs available for use: {n_cpus}")
    return n_cpus

def _get_local_cpu_reserve(total_cpus: int) -> int:
    """Determine how many CPUs to reserve for system use on a local machine.

    Attempts to read a YAML config file ("RunConfig.yml") for a user-defined
    reserve value under the 'MultiProcessing' section. If the value is -1, uses
    default logic based on total core count. If the value is invalid or missing,
    falls back to default logic.

    Default reserve rules:
        - 0 reserved if only 1 core
        - 1 reserved if 2-6 cores
        - 2 reserved if more than 6 cores

    Args:
        total_cpus (int): The total number of logical CPUs on the local machine.

    Returns:
        int: The number of CPUs to reserve (0 or more, less than total_cpus).
    """
    # Default behavior based on core count
    def default_reserve():
        if total_cpus == 1:
            return 0
        elif total_cpus <= 6:
            return 1
        else:
            return 2
        
    # get configurations
    config_loader = ConfigLoader("RunConfig.yml")
    try:
        # number of CPUs to reserve when multiprocessing
        cpu_reserve: int = config_loader.get('MultiProcessing', 'cpu_reserve')
    except Exception as e:
        logger.exception(e)
        raise

    if cpu_reserve == -1:
        logger.debug("cpu_reserve set to -1 — using default reserve logic.")
        return default_reserve()

    if 0 <= cpu_reserve < total_cpus:
        if cpu_reserve == 0:
            logger.warning("CPU reserve is set to 0, which may lead to system unresponsiveness.")
        return cpu_reserve

    logger.warning(f"Invalid cpu_reserve={cpu_reserve}; falling back to default reserve.")
    return default_reserve()
