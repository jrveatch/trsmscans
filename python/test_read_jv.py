# script to test computation time to read tsv files

import time

start = time.time()

# list of files to read in
filenames = [
    'data/TRSMBroken_0001_WIDTH.tsv',
    'data/TRSMBroken_0002_WIDTH.tsv',
    'data/TRSMBroken_0003_WIDTH.tsv',
    'data/TRSMBroken_0004_WIDTH.tsv',
    'data/TRSMBroken_0005_WIDTH.tsv',
    'data/TRSMBroken_0006_WIDTH.tsv',
    'data/TRSMBroken_0007_WIDTH.tsv',
    'data/TRSMBroken_0008_WIDTH.tsv',
    'data/TRSMBroken_0009_WIDTH.tsv',
    'data/TRSMBroken_0010_WIDTH.tsv'
]

# put code here to read all tsv files into numpy arrays

import columns
import arrays

# get list of column numbers
cols = columns.Columns('data/TRSMBroken_0001_WIDTH.tsv')

# loop over list of filenames
for filename in filenames:

    # indicate which file is being read
    print("Reading " + filename)

    # get arrays from active file
    arr = arrays.Arrays(filename,cols)

    # check that alll 65 columns are correctly loaded
    print("Found " + str(len(vars(arr))) + " arrays")

    # check length of an array
    print("Arrays have " + str(arr.mH3.size) + " elements")

end = time.time()

print("The execution time for reading tsv files into numpy arrays :",
      (end-start) * 10**3, "ms")
