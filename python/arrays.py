
# import numpy library as np
import numpy as np

class Arrays:

    def __init__(self,filename):

        self.headers = []

        self.filename = filename

        self.loadHeaders(filename)

    def loadHeaders(self,filename):

        with open(filename,'r') as file:
            header_line = file.readline().strip()
            self.headers = header_line.split('\t')

        if self.headers[0] != 'idx':
            self.headers.insert(0, 'idx')

    def getHeaders(self):
        return self.headers

    def loadArrays(self,filename=""):

        if filename:
            self.filename = filename

        if not self.headers:
            print("Headers were not loaded, loading now")
            self.loadHeaders(self.filename)

        self.data = np.genfromtxt(self.filename, delimiter='\t', dtype=None, names=self.headers, encoding=None, skip_header=1)

    # get an array
    def getArray(self,arr_name):
        return self.data[arr_name]

    # set the values of an array
    def setArray(self,arr_name,new_array):
        self.data[arr_name] = new_array

    # write arrays to a new file
    def writeFile(self,filename):
        with open(filename,'w') as f:
            # write headers
            f.write('\t'.join(self.headers) + '\n')
            # write data
            np.savetxt(f, self.data, delimiter='\t', fmt='%s')
