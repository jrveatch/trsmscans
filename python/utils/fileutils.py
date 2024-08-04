
import os
from masses import Masses

# get scan directory
def scan_dir(modelname: str,
             decay: str,
             masses: 'Masses') -> str:
    return os.environ['OUTPUTDIR']+modelname+"/scan/"+decay+"/"+str(masses)+"/"

# get prescan directory
def prescan_dir(modelname: str,
                masses: 'Masses') -> str:
    return os.environ['OUTPUTDIR']+modelname+"/prescan/"+str(masses)+"/"

# get prescan .tsv file
def prescan_tsv(modelname: str,
                masses: 'Masses') -> str:
    return prescan_dir(modelname=modelname,masses=masses)+modelname+"_prescan.tsv"

# get plots directory
def plots_dir(modelname: str,
              decay: str,
              masses: 'Masses'):
    return os.environ['OUTPUTDIR']+modelname+"/plots/"+decay+"/"+str(masses)+"/"
