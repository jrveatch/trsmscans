import argparse
import os
import shutil
import subprocess
import uuid

import pandas as pd

from masses import Masses
from parse import Parse

ROOT = os.path.dirname(__file__)
ROOT_OUTPUT = os.path.abspath(os.path.join(ROOT, "../run/output/"))
PATH_SCAN = os.path.join(ROOT, "scan.py")

parser = argparse.ArgumentParser(description="Batch scan and export")
parser.add_argument("-outpath", type=str)
parser.add_argument("-iters", type=int)
parser.add_argument("-X", type=int)
parser.add_argument("-S", type=int)
parser.add_argument("-d", type=str)
parser.add_argument("-n", type=int)

args = parser.parse_args()

UUID = uuid.uuid1()

PATH_OUT_SCAN = os.path.join(ROOT_OUTPUT, f"./TRSMBroken/scan/SbbHtautau/X{args.X}_S{args.S}/files/TRSMBroken_test_0000.tsv")

PATH_OUT_RESULT = os.path.abspath(os.path.join(os.getcwd(), args.outpath, "batch_scan_export", "output", str(UUID)))

# Ensure environment is set up properly
#print("Activating trsm_venv env...")
#subprocess.run(
#	shell=True,
#	args=["source", os.path.abspath(os.path.join(ROOT, "../trsm_venv/bin/activate"))]
#)
#print("Done")

#print("Running setup.sh...")
#subprocess.run(
#	shell=True,
#	args=["source", "../setup.sh"]
#)
#print("Done...")

# Make dir if not exists
print("Creating output dir " + PATH_OUT_RESULT + " ...")
if (not os.path.exists(PATH_OUT_RESULT)):
	os.makedirs(PATH_OUT_RESULT)
print("Done")

for i in range(args.iters):
	print("i = " + str(i))
	print("Deleting existing output...")

	if (os.path.exists(ROOT_OUTPUT)):
		shutil.rmtree(ROOT_OUTPUT)

	print("Done")

	print("Running scan subprocess...")
	subprocess.run(
		shell=True,
		args=[PATH_SCAN + f" -X {args.X} -S {args.S} -M TRSMBroken -d {args.d} -n {args.n} -i 1 -m"]
	)

	print("Done")

	print("Calling parse")

	masses = Masses(mX=args.X, mS=args.S, mH=125.09)
	parse = Parse(masses=masses, decay=args.d, modelname="TRSMBroken", filename=PATH_OUT_SCAN)

	target = parse.getXB(decay=args.d)
	features = parse.getParameters()
	xb = parse.getXB()

	print("Done")

	path = os.path.join(PATH_OUT_RESULT, f"scan_{i}.tsv")

	print(f"Writing tsv file {path} ...")

	df = pd.DataFrame.from_dict(features)
	df.insert(len(df.columns), 'xb', xb)

	df.to_csv(path, sep="\t", index=False)

	print("Done")
