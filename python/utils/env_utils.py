
# standard libraries
import os

def output_dir() -> str:
    """
    Get path to output directory.
    """
    return os.environ['OUTPUT_DIR']

def config_dir() -> str:
    """
    Get path to config directory.
    """
    return os.environ['CONFIG_DIR']

def data_dir() -> str:
    """
    Get path to data directory.
    """
    return os.environ['DATA_DIR']

def htcondor_dir() -> str:
    """
    Get path to htcondor directory.
    """
    return os.environ['HTCONDOR_DIR']

def externals_dir() -> str:
    """
    Get path to externals directory.
    """
    return os.environ['EXTERNALS_DIR']

def hbdataset_dir() -> str:
    """
    Get path to HBDataset directory.
    """
    if "HBDATASET_PATH" in os.environ:
        return os.environ['HBDATASET_PATH']
    else:
        return os.path.join(externals_dir(),"hbdataset")

def hsdataset_dir() -> str:
    """
    Get path to HSDataset directory.
    """
    if "HSDATASET_PATH" in os.environ:
        return os.environ['HSDATASET_PATH']
    else:
        return os.path.join(externals_dir(),"hsdataset")
