import numpy as np
import matplotlib.pyplot as plt

import parse

decay = "SbbHtautau"
xmass = "1000"
smass = "300"
niter = 2

prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"

filename = prescan

# get arrays object
parser = parse.Parse(filename,HMass=125,SMass=float(smass))

thetahS, thetahX, thetaSX, vs, vx = parser.getvars()

xb = parser.getxb(decay)

plt.scatter(thetahS,thetahX,s=30,c="hotpink")

plt.show()
