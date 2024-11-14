
import os
import yaml
from typing import Any, Optional
import logging

class ConfigLoader:

    def __init__(self,
                 config_file_name: str,
                 config_path: str = ""):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # if not config path is given, use default path defined as environment variable
        if not config_path:
            config_path = os.environ['CONFIGDIR']

        self.logger.debug(f"Loading configuration from {config_path + config_file_name}\n")

        self.config = self.load_config(config_path + config_file_name)

    def load_config(self,
                    path: str) -> dict[str, Any]:
        # loads the YAML configuration file and returns the configuration as a dictionary.
        try:
            with open(path, 'r') as config_file:
                return yaml.safe_load(config_file) or {}  # Ensure it returns a dictionary, even if empty
        except FileNotFoundError:
            print(f"Error: Configuration file '{path}' not found.")
            raise  # Re-raise the exception to halt the program or handle as needed
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse YAML file '{path}'.\nDetails: {e}")
            raise  # Re-raise to handle upstream
        except Exception as e:
            print(f"Unexpected error while loading config file '{path}': {e}")
            raise

    def get(self,
            section: str,
            key: str,
            default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieve a specific setting from the config with an optional default value.
        
        Args:
            section: The section of the configuration to retrieve.
            key: The specific key within the section.
            default: The default value to return if the key is not found.
        
        Returns:
            The value from the configuration if found, otherwise the default value.
        """
        try:
            value = self.config.get(section, {}).get(key, default)
            if value is None:
                raise KeyError(f"Missing configuration for '{section}.{key}'")
            return value
        except KeyError as e:
            print(f"Error: {e}")
            raise  # Depending on your needs, you can choose to raise or handle differently
        except Exception as e:
            print(f"Unexpected error accessing config key '{section}.{key}': {e}")
            raise
