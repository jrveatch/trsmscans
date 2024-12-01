
import pandas as pd

index_label = "idx"

# load tsv columns into a pandas dataframe
def get_df(file_name: str) -> pd.DataFrame:

    # load the file into a dataframe
    dataframe = pd.read_csv(file_name,
                            sep='\t',
                            header=0)
    
    # drop first column to avoid compounding indices
    dataframe = dataframe.iloc[:, 1:]
    
    return dataframe

# get header as tab separated string including idx
def get_header_string(dataframe: pd.DataFrame) -> str:
    return "\t".join([index_label] + dataframe.columns.tolist())

# write arrays to a new file
def write_to_tsv(dataframe: pd.DataFrame,
                 file_name: str
                ) -> None:

    dataframe.to_csv(file_name,
                     sep='\t',
                     index=True,
                     index_label=index_label)
