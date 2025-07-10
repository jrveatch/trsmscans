
# standard libraries
import os
from typing import Any, Dict, Optional

# third-party libraries
import yaml

# local modules
from utils.env_utils import config_dir

# get logger
import logging
logger = logging.getLogger(__name__)

_MISSING = object()  # sentinel value

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

        # if not config path is given, use default path defined as environment variable
        if config_path is None:
            config_path = config_dir()

        logger.debug(f"Loading configuration from {os.path.join(config_path,config_file_name)}")

        self.config = self.load_config(os.path.join(config_path,config_file_name))
        self.level_index = self.build_level_index(self.config)

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
            logger.exception(f"Configuration file '{path}' not found.")
            raise  # Re-raise the exception to halt the program or handle as needed
        except yaml.YAMLError:
            logger.exception(f"Failed to parse YAML file '{path}'.")
            raise  # Re-raise to handle upstream
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise

    def get(self,
            section: str,
            key: Optional[str] = None,
            default: Any = _MISSING) -> Any:
        """
        Retrieve a configuration value from a specified section.

        If a key is provided, returns the corresponding value. If the key is not
        found, returns the default if specified, otherwise raises KeyError.
        
        If no key is provided, returns the entire section as a dictionary.

        Args:
            section (str): The section name in the configuration.
            key (Optional[str], optional): The key within the section. If omitted,
                                           the entire section dict is returned.
            default (Any, optional): Fallback value if the key is missing.
                                     If not set, a missing key raises KeyError.

        Returns:
            Any: The configuration value for the given section and key, or the
                entire section dictionary if key is omitted.

        Raises:
            KeyError: If the section or key is missing and no default is provided.
            Exception: For unexpected access errors.
        """

        try:
            section_dict = self.config.get(section)
            if section_dict is None:
                if default is not _MISSING:
                    return default
                raise KeyError(f"Missing configuration section: '{section}'")

            if key is None:
                return section_dict

            value = section_dict.get(key, _MISSING)
            if value is not _MISSING:
                return value

            if default is not _MISSING:
                return default

            raise KeyError(f"Missing configuration for '{section}.{key}'")

        except Exception as e:
            logger.exception(e)
            raise

    def build_level_index(self,
                          config: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Construct a level-indexed configuration mapping from a hierarchical config.

        This function transforms a level-based configuration structure into a 
        parameter-centric lookup index. The resulting dictionary enables fast 
        access to the values of individual parameters across different precision 
        levels within a section.

        For example, given a section like:
        
            zoom:
            coarse:
                param_a: 1
                param_b: 2
            fine:
                param_a: 10
                param_b: 20

        The resulting index will be:
        
            {
            "zoom": {
                "param_a": {
                "coarse": 1,
                "fine": 10
                },
                "param_b": {
                "coarse": 2,
                "fine": 20
                }
            }
            }

        Args:
            config (Dict[str, Any]): The full configuration dictionary loaded from YAML.

        Returns:
            Dict[str, Dict[str, Dict[str, Any]]]: 
                A nested dictionary where each section maps to a dictionary of parameters,
                and each parameter maps to a dictionary of {level: value} pairs.
        """
        index = {}
        for section, section_data in config.items():
            if not isinstance(section_data, dict):
                continue
            param_index = {}
            for level, params in section_data.items():
                if not isinstance(params, dict):
                    continue
                for param, value in params.items():
                    param_index.setdefault(param, {})[level] = value
            index[section] = param_index
        return index
    
    def get_param_levels(self,
                         section: str,
                         param: str) -> Dict[str, Any]:
        """
        Retrieve a dictionary of {level: value} for a given parameter in a section.

        Args:
            section (str): The top-level section (e.g., 'zoom').
            param (str): The name of the parameter (e.g., 'parameter_zoom_rate').

        Returns:
            Dict[str, Any]: Mapping of level → parameter value.

        Raises:
            KeyError: If section or parameter does not exist.
        """
        try:
            section_index = self.level_index.get(section)
            if section_index is None:
                raise KeyError(f"Section '{section}' not found in configuration index.")

            param_levels = section_index.get(param)
            if param_levels is None:
                raise KeyError(f"Parameter '{param}' not found under section '{section}'.")

            return param_levels

        except KeyError as e:
            logger.error(e)
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while retrieving parameter levels for '{param}' in '{section}': {e}")
            raise
