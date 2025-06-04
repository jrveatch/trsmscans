
# standard libraries
import logging
from typing import cast, List

# third-party libraries
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
    dataframe = pd.read_csv(file_name,
                            sep='\t',
                            header=0)

    # drop first column to avoid compounding indices
    dataframe = dataframe.iloc[:, 1:]

    return dataframe

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
    except Exception as e:
        logger.exception(f"Error writing to file {file_name}")
        raise
