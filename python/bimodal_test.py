
import parse
import numpy as np
import matplotlib.pyplot as plt
import diptest

filename = "output/prescan/X1000_S300/TRSMBroken_prescan.tsv"

parser = parse.Parse(filename,125,300)

xb = parser.getxb("SbbHtautau")

thetahS, thetahX, thetaSX, vs, vx = parser.getvars()

percentile_threshold = 99

threshold_value = np.percentile(xb, percentile_threshold)

xb_selected = xb[xb > threshold_value]
thetahS_selected = thetahS[xb > threshold_value]
thetahX_selected = thetahX[xb > threshold_value]
thetaSX_selected = thetaSX[xb > threshold_value]
vs_selected = vs[xb > threshold_value]
vx_selected = vx[xb > threshold_value]

dip, pval = diptest.diptest(thetahS_selected)

print("dip =",dip)
print("p-value =",pval)

plt.scatter(thetahS_selected,xb_selected,s=10,c="hotpink")
plt.show()
