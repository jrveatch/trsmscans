
import numpy as np
from numpy.typing import NDArray
import random
from io import StringIO

class Arrays:

    def __init__(self,
                 file_name: str):

        # store file name
        self.__file_name = file_name
    
        # empty headers list
        self.__headers: list[str] = []

        # empty array data
        self.__data: NDArray = None

        # load tsv column headers
        self.__load_headers()

        # load tsv data into arrays
        self.load_arrays()

    # get array data
    def data(self,
             column: str = "") -> NDArray:
        if column:
            return self.__data[column]
        else:
            return self.__data

    # load tsv column headers into a list
    def __load_headers(self) -> None:

        # read column headers into list
        with open(self.__file_name,'r') as file:
            header_line = file.readline().strip()
            self.__headers = header_line.split('\t')

        # make sure first column has 'idx' as header
        if self.__headers[0] != 'idx':
            self.__headers.insert(0, 'idx')

    # load tsv columns into a numpy array
    def load_arrays(self,
                    file_name: str = "",
                    num_lines: int = -1) -> None:

        # if a new file name is provided, store it as class object
        if file_name:
            self.__file_name = file_name

        # if headers have not be loaded, load them now
        if not self.__headers:
            print("Headers were not loaded, loading now")
            self.load_headers()

        with open(self.__file_name, 'r') as f:
            _ = f.readline()
            lines = f.readlines()

        if num_lines != -1:
            selected_lines = random.sample(lines, num_lines)
            selected_lines_str = ''.join(selected_lines)

            self.__data = np.genfromtxt(StringIO(selected_lines_str),
                                        delimiter='\t',
                                        dtype=None,
                                        names=self.__headers,
                                        encoding=None)
        else:
            # create numpy array from the tsv
            self.__data = np.genfromtxt(self.__file_name,
                                        delimiter='\t',
                                        dtype=None,
                                        names=self.__headers,
                                        encoding=None,
                                        skip_header=1)

    # get an array
    def get_array(self,
                  arr_name: str) -> NDArray:
        return self.__data[arr_name]
    
    # get all arrays
    def get_all_arrays(self) -> NDArray:
        return self.__data

    # set the values of an array
    def set_array(self,
                 arr_name: str,
                 new_array: NDArray) -> None:
        self.__data[arr_name] = new_array

    # write arrays to a new file
    def write_file(self,
                   file_name: str) -> None:
        # open output file
        with open(file_name,'w') as f:
            # write headers
            f.write('\t'.join(self.__headers) + '\n')
            # write data
            np.savetxt(f, self.__data, delimiter='\t', fmt='%s')
