
# search strings
import re

# column indices
import columns

def filterwidths(filename, cols:columns.Columns, maxwidth):

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

            # calculate fractional widths
            width1 = data[cols.w_H1] / data[cols.mH1]
            width2 = data[cols.w_H2] / data[cols.mH2]
            width3 = data[cols.w_H3] / data[cols.mH3]

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
