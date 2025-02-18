
# standard libraries
import os

def output_dir() -> str:
    """
    Get path to output directory.
    """
    return os.environ['OUTPUTDIR']

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
