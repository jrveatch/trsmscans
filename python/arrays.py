
# import numpy library as np
import numpy as np

class Arrays:

    def __init__(self,filename):

        # store filename
        self.filename = filename

        # load tsv column headers
        self.loadHeaders()

        # load tsv data into arrays
        self.loadArrays()

    # load tsv column headers into a list
    def loadHeaders(self):
        
        # empty headers list
        self.headers = []

        # read column headers into list
        with open(self.filename,'r') as file:
            header_line = file.readline().strip()
            self.headers = header_line.split('\t')

        # make sure first column has 'idx' as header
        if self.headers[0] != 'idx':
            self.headers.insert(0, 'idx')

    def getHeaders(self):
        return self.headers

    # load tsv columns into a numpy array
    def loadArrays(self,filename=""):

        # if a new filename is provided, store it as class object
        if filename:
            self.filename = filename

        # if headers have not be loaded, load them now
        if not self.headers:
            print("Headers were not loaded, loading now")
            self.loadHeaders()

        # create numpy array from the tsv
        self.data = np.genfromtxt(self.filename, delimiter='\t', dtype=None, names=self.headers, encoding=None, skip_header=1)

    # get an array
    def getArray(self,arr_name):
        return self.data[arr_name]

    # set the values of an array
    def setArray(self,arr_name,new_array):
        self.data[arr_name] = new_array

    # write arrays to a new file
    def writeFile(self,filename):
        # open output file
        with open(filename,'w') as f:
            # write headers
            f.write('\t'.join(self.headers) + '\n')
            # write data
            np.savetxt(f, self.data, delimiter='\t', fmt='%s')
