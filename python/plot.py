import numpy as np
import matplotlib.pyplot as plt

import columns
import parse

decay = "H2bbH1tautau"
xmass = "500"
smass = "300"
niter = 16

prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"
# get list of column numbers
cols = columns.Columns(prescan)

for iter in range(niter):
    identifier = f"{iter:04d}"

    print(identifier)

    if iter == 0:
        filename = prescan

    else:
        filename = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_"+identifier+"_BOUNDS.tsv"

    # get arrays object
    parser = parse.Parse(filename,cols)

    thetahS, thetahX, thetaSX, vs, vx = parser.getvars()

    xb = parser.getxb(decay)

    color = str(0.8*(1 - iter/niter))

    print(color)

    plt.scatter(thetahS,thetahX,s=10,c=color)

plt.scatter(thetahS,thetahX,s=30,c="hotpink")

plt.show()
