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

# Setup logging configuration
def setup_logging(level=logging.INFO, log_format="%(levelname)s: %(message)s"):
    logging.basicConfig(level=level, format=log_format)
    # Example: Set default level to VERBOSE if needed
    logging.getLogger().setLevel(level)