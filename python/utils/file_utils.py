
# standard libraries
import os

# local modules
from utils.masses import Masses

# get scan directory
def scan_dir(model_name: str,
             decay: str,
             masses: 'Masses') -> str:
    return os.environ['OUTPUTDIR']+model_name+f"/scan/{decay}/{masses}/"

# get prescan directory
def prescan_dir(model_name: str,
                masses: 'Masses') -> str:
    return os.environ['OUTPUTDIR']+model_name+f"/prescan/{masses}/"

# get prescan .tsv file
def prescan_tsv(model_name: str,
                masses: 'Masses') -> str:
    return prescan_dir(model_name=model_name,masses=masses)+model_name+"_prescan.tsv"

# get plots directory
def plots_dir(model_name: str,
              decay: str,
              masses: 'Masses') -> str:
    return os.environ['OUTPUTDIR']+model_name+f"/plots/{decay}/{masses}/"
