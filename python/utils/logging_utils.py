
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

    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up logging to file and console
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, mode='w'),  # File logging
            logging.StreamHandler()                   # Console logging
        ]
    )