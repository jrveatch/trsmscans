import importlib
import os

import pandas as pd

from masses import Masses
from parse import Parse

## Note: It would be a good idea to run 'sudo chmod 777 data' from the 'run' directory before attempting to run this file, or else the data file will not be written...

mX=1001
mS=301

ROOT_PATH = os.path.dirname(__file__)
TEST_FILE_REL = f'../run/output/TRSMBroken/scan/SbbHtautau/X{mX}_S{mS}/files/TRSMBroken_test_0000.tsv'

# Using relative file here so that we can access it from any machine
# os.path.dirname(__file__) gets the absolute path of the current file that we can join with our relative dir
file_path = os.path.abspath(os.path.join(ROOT_PATH, TEST_FILE_REL))

print("file path = " + str(file_path))

masses = Masses(mX=mX, mS=mS, mH=125.09)
parse = Parse(masses=masses, decay="SbbHtautau", modelname="TRSMBroken", filename=file_path)

target = parse.getXB(decay="SbbHtautau")
features = parse.getParameters()
xb = parse.getXB()

df = pd.DataFrame.from_dict(features)
df.insert(len(df.columns), 'xb', xb)

DATA_DIR_REL = "../run/data"
out_path = os.path.abspath(os.path.join(ROOT_PATH, DATA_DIR_REL, "test.tsv"))
df.to_csv(out_path, sep="\t", index=False)
print("File written...")
