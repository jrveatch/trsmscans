
import parse
import numpy as np
import matplotlib.pyplot as plt
import diptest

filename = "output/prescan/X1000_S300/TRSMBroken_prescan.tsv"

parser = parse.Parse(filename,125,300,"SbbHtautau")

xb = parser.getxb("SbbHtautau")

tHS, tHX, tSX, vs, vx = parser.getvars()

isUnimodal = parser.isBimodal("tHS")

print(isUnimodal)

plt.scatter(tHS,xb,s=10,c="hotpink")
plt.show()
