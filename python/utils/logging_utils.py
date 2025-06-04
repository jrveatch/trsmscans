
# standard libraries
import logging
import os
from typing import Any, List

# Define the numeric value for VERBOSE
VERBOSE_LEVEL = 5  # Below DEBUG (10)

# Add VERBOSE level name to logging
logging.addLevelName(VERBOSE_LEVEL, "VERBOSE")

# Define the verbose method for Logger class
def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_LEVEL):
        self._log(VERBOSE_LEVEL, message, args, **kwargs)

# Add the method to the Logger class
logging.Logger.verbose = verbose

# Add VERBOSE as an attribute to the logging module
logging.VERBOSE = VERBOSE_LEVEL

# Define a mapping of string levels to logging levels
LOG_LEVELS = {
    "verbose": logging.VERBOSE,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# Define a custom formatter class
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Use a simple format for specific messages
        if hasattr(record, "skip_level") and record.skip_level:
            return record.getMessage()
        return super().format(record)

def setup_logging(log_file: str,
                  level = logging.INFO,
                  log_format = None) -> None:
    """
    Set up logging to output to both a file and the console.

    Args:
        log_file (str): Path to the log file.
        level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
        log_format (str): Custom format for log messages. Defaults to a standard format.
    """

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Define the log message format
    if log_format is None:
        log_format = '%(levelname)s: %(message)s'

    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create the log file directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create handlers
    file_handler = logging.FileHandler(log_file, mode='w') # File handler
    console_handler = logging.StreamHandler() # Console handler

    # Use the custom formatter
    formatter = CustomFormatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def format_table(headers: List[str],
                 rows: List[List[Any]]) -> str:
    """
    Format a table as a string.

    Args:
        headers (List[str]): List of column headers.
        rows (List[List[Any]]): List of rows, where each row is a list of column values.

    Returns:
        str: Nicely formatted table as a string.
    """

    # Calculate column widths
    column_widths = [max(len(str(item)) for item in [header] + [row[i] for row in rows]) for i, header in enumerate(headers)]

    # Create a horizontal separator
    separator = " | ".join("-" * width for width in column_widths)

    # Format the header row
    header_row = " | ".join(f"{header:<{width}}" for header, width in zip(headers, column_widths))

    # Format the data rows
    data_rows = [" | ".join(f"{str(item):<{width}}" for item, width in zip(row, column_widths)) for row in rows]

    # Combine everything into a table string
    table = f"{header_row}\n{separator}\n" + "\n".join(data_rows) + "\n"
    return table

def log_table(logger: logging.Logger,
              headers: List[str],
              rows: List[List[Any]],
              level: int = logging.INFO) -> None:
    """
    Log a nicely formatted table.

    Args:
        logger (logging.Logger): Logger instance.
        headers (List[str]): List of column headers.
        rows (List[List[Any]]): List of rows, where each row is a list of column values.
        level (int): Logging level (default: logging.INFO).
    """

    table_str = format_table(headers, rows)
    extra = {"skip_level": True}
    if logger.isEnabledFor(level):
        logger.log(level, f"\n{table_str}", extra=extra)
