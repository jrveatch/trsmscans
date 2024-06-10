
import os
from masses import Masses

# get scan directory
def scanDir(modelname,
            decay,
            masses: 'Masses'):
    return os.environ['OUTPUTDIR']+modelname+"/scan/"+decay+"/"+str(masses)+"/"

# get prescan directory
def prescanDir(modelname,
               masses: 'Masses'):
    return os.environ['OUTPUTDIR']+modelname+"/prescan/"+str(masses)+"/"

# get prescan .tsv file
def prescanTSV(modelname,
               masses: 'Masses'):
    return prescanDir(modelname=modelname,masses=masses)+modelname+"_prescan.tsv"
