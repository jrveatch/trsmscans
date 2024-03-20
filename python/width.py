
# search strings
import re

def filterwidths(filename, headers, maxwidth):

    infile = open(filename+"_RAW.tsv","r")
    outfile = open(filename+"_WIDTH.tsv","w")

    npoints = 0
    npass = 0
 
    for line in infile:

        write = False

        # skip lines with letters other than "e"
        if re.search('[a-df-zA-Z]', line):
            write = True

        else:
            # count lines going into filter
            npoints += 1

            # parse line into numerical values
            data = [float(x) for x in line.split()]

            # get indices of each data column
            idx_w_H1 = headers.index('w_H1')
            idx_w_H2 = headers.index('w_H2')
            idx_w_H3 = headers.index('w_H3')

            idx_mH1 = headers.index('mH1')
            idx_mH2 = headers.index('mH2')
            idx_mH3 = headers.index('mH3')

            # calculate fractional widths
            width1 = data[idx_w_H1] / data[idx_mH1]
            width2 = data[idx_w_H2] / data[idx_mH2]
            width3 = data[idx_w_H3] / data[idx_mH3]

            # skip line if width is over max
            if width1 > maxwidth:
                continue
            if width2 > maxwidth:
                continue
            if width3 > maxwidth:
                continue

            # count lines that pass
            npass += 1

            write = True

        # write line to output file
        if write:
            outfile.write(line)

    infile.close()
    outfile.close()

    return npoints, npass
