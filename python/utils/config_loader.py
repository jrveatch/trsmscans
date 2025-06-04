
# standard libraries
import logging
import os
from typing import Any, Dict, Optional

# third-party libraries
import yaml

# local modules
from utils.env_utils import config_dir

class ConfigLoader:
    """
    Loads and provides access to structured configuration data from a YAML file.

    This class supports hierarchical configuration structures, logging of load events,
    error handling for missing or malformed files, and value retrieval with validation.
    """

    def __init__(self,
                 config_file_name: str,
                 config_path: Optional[str] = None):
        """
        Initialize the ConfigLoader with a YAML configuration file.

        Args:
            config_file_name (str): Name of the configuration file to load.
            config_path (str, optional): Path to the configuration directory.
                If not provided, a default path from the environment is used.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            yaml.YAMLError: If there is an error parsing the YAML file.
            Exception: For other unexpected errors during loading.
        """

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # if not config path is given, use default path defined as environment variable
        if config_path is None:
            config_path = config_dir()

        self.logger.info(f"Loading configuration from {os.path.join(config_path,config_file_name)}\n")

        self.config = self.load_config(os.path.join(config_path,config_file_name))

    def load_config(self,
                    path: str) -> Dict[str, Any]:

        """
        Load a YAML configuration file.

        Args:
            path (str): Full path to the YAML configuration file.

        Returns:
            Dict[str, Any]: The parsed configuration data.

        Raises:
            FileNotFoundError: If the file does not exist.
            yaml.YAMLError: If the YAML content is invalid.
            Exception: For any other unexpected errors.
        """

        try:
            with open(path, 'r') as config_file:
                return yaml.safe_load(config_file) or {}  # Ensure it returns a dictionary, even if empty
        except FileNotFoundError:
            self.logger.exception(f"Configuration file '{path}' not found.")
            raise  # Re-raise the exception to halt the program or handle as needed
        except yaml.YAMLError as e:
            self.logger.exception(f"Failed to parse YAML file '{path}'.")
            raise  # Re-raise to handle upstream
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            raise

    def get(self,
            section: str,
            key: str) -> Any:
        """
        Retrieve a configuration value from a given section and key.

        Args:
            section (str): The section name in the configuration file.
            key (str): The key name within the section.

        Returns:
            Any: The value from the configuration.

        Raises:
            KeyError: If the section or key is missing.
            Exception: For unexpected access errors.
        """

        try:
            value = self.config.get(section, {}).get(key)
            if value is None:
                raise KeyError(f"Missing configuration for '{section}.{key}'")
        except KeyError as e:
            self.logger.exception("Missing configuration key")
            raise  # Depending on your needs, you can choose to raise or handle differently
        except Exception as e:
            self.logger.exception(f"Unexpected error: {e}")
            raise
        else:
            return value
