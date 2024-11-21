
import pandas as pd
from typing import Union

class Arrays:

    def __init__(self,
                 file_name: str):

        # store file name
        self.__file_name = file_name

        # load tsv data into arrays
        self.load_arrays()

    # get array data
    def data(self,
             column: Union[str, None] = None) -> Union[pd.Series, pd.DataFrame]:
        if column:
            return self.dataframe[column]
        else:
            return self.dataframe

    # get header as tab separated string
    def get_header_string(self) -> str:
        return "\t".join(['idx'] + self.dataframe.columns.tolist())

    # load tsv columns into a pandas dataframe
    def load_arrays(self,
                    file_name: str = ""
                    ) -> None:

        # if a new file name is provided, store it as class object
        if file_name:
            self.__file_name = file_name

        # load the file into a dataframe
        self.dataframe = pd.read_csv(self.__file_name,sep='\t',header=0,usecols=lambda col: col != 'idx' and col != '')

    # sample the dataframe to get a number of random rows
    def sample_rows(self,
                    num_rows: int) -> pd.DataFrame:
        return self.dataframe.sample(n=num_rows)

    # set the values of an array
    def set_array(self,
                 column_name: str,
                 new_values: pd.Series
                 #new_array: NDArray
                 ) -> None:
        self.dataframe[column_name] = new_values

    # write arrays to a new file
    def write_file(self,
                   file_name: str) -> None:
        self.dataframe.to_csv(file_name, sep='\t', index=True, index_label='idx')
