
# standard libraries
import logging

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

# Setup logging configuration
def setup_logging(log_file: str,
                  level = logging.INFO,
                  log_format = None) -> None:
    """
    Set up logging to output to both a file and the console.

    Parameters:
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

    formatter = logging.Formatter(log_format)

    # Ensure the log file is overwritten
    with open(log_file, 'w'):
        pass  # This clears the file contents

    # Create file handler for logging to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Create console handler for logging to the screen
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Remove any existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
