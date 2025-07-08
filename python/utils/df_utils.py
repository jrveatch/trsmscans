
# standard libraries
import logging
import os
from typing import cast, List

# third-party libraries
import numpy as np
import pandas as pd

# get logger
logger = logging.getLogger(__name__)

index_label: str = "idx"

def get_df(file_name: str) -> pd.DataFrame:
    """
    Load a tab-separated file into a DataFrame and drop the first column
    to remove an unwanted index column.

    Args:
        file_name (str): Path to the .tsv file.

    Returns:
        pd.DataFrame: Cleaned DataFrame without the first column.
    """

    # load the file into a dataframe
    return pd.read_csv(file_name,
                       sep='\t',
                       index_col=0)

def load_scanner_output(input_files: List[str]) -> pd.DataFrame:
    """
    Reads and merges multiple .tsv files into a single DataFrame.

    Args:
        input_files (List[str]): List of input .tsv files with their paths

    Returns:
        pd.DataFrame: Merged DataFrame containing all rows from all found .tsv files.
    """
    dfs = []
    for f in input_files:
        if os.path.exists(f):
            df = pd.read_csv(f,
                             sep="\t",
                             index_col=0)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def get_header_string(dataframe: pd.DataFrame) -> str:
    """
    Get the header of the DataFrame as a tab-separated string including index column.

    Args:
        dataframe (pd.DataFrame): The DataFrame to extract the header from.

    Returns:
        str: Tab-separated string of the header including index column.
    """
    return "\t".join([index_label, *cast(List[str], dataframe.columns.tolist())])

# write arrays to a new file
def write_to_tsv(dataframe: pd.DataFrame,
                 file_name: str) -> None:
    """
    Write a DataFrame to a tab-separated file.

    Args:
        dataframe (pd.DataFrame): The DataFrame to write.
        file_name (str): Path to the output .tsv file.
    """

    try:
        dataframe.to_csv(file_name,
                         sep='\t',
                         index=True,
                         index_label=index_label)
    except Exception:
        logger.exception(f"Error writing to file {file_name}")
        raise

def chunk_dataframe(df: pd.DataFrame,
                    n_chunks: int) -> List[pd.DataFrame]:
    """
    Splits a DataFrame into approximately equal-sized chunks.

    Args:
        df (pd.DataFrame): DataFrame to split.
        n_chunks (int): Number of chunks.

    Returns:
        List[pd.DataFrame]: List of DataFrame chunks.
    """
    chunk_size = int(np.ceil(len(df) / n_chunks))
    return [df.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(n_chunks)]
