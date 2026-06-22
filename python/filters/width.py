#!/usr/bin/env python3

"""
WidthFilter class for applying scalar particle width constraints in model scans.

Uses thresholds from a config file to flag parameter points where widths exceed
allowed fractions of the scalar masses.
"""

# third-party libraries
import numpy as np
import pandas as pd

# local modules
from utils.config_loader import ConfigLoader
from utils.model import Model

# get logger
import logging
logger = logging.getLogger(__name__)

class WidthFilter:
    """
    Applies width-based filtering to scalar particles in a model scan.

    This class loads width thresholds from a model-specific config file and uses them
    to flag parameter points in a scan DataFrame where any scalar particle width
    exceeds an allowed fraction of its mass.
    """
    def __init__(self,
                 model: Model):
        """
        Initializes the WidthFilter with model-specific scalar names and width thresholds.

        Args:
            model (Model): The scalar model object providing naming conventions and config key.
            
        Raises:
            KeyError: If required threshold keys are missing from the config.
            Exception: For unexpected errors during config loading.
        """
    
        self.model = model

        # Scalar name mappings (e.g., H1, H2, H3)
        self.HName = model.get_ordered_scalar_name('H')
        self.SName = model.get_ordered_scalar_name('S')
        self.XName = model.get_ordered_scalar_name('X')

        # Load configuration thresholds
        model_config = ConfigLoader(f"{model.name}_default.yml")
        try:
            self.thresholds: np.ndarray = np.array([
                model_config.get('width', 'max_width_H'),
                model_config.get('width', 'max_width_S'),
                model_config.get('width', 'max_width_X'),
            ])
        except Exception:
            logger.exception("Failed to load width thresholds from config.")
            raise

    def apply(self,
                   data: pd.DataFrame,
                   header: str) -> pd.Series:
        """
        Evaluate the width filter for each scan point.

        A scan point passes the width filter if the widths of all scalar states
        are less than the corresponding mass multiplied by the configured width
        threshold. The input DataFrame is not modified.

        Args:
            data (pd.DataFrame): Scan points to evaluate. The DataFrame must
                contain the required mass and width columns for all scalar states.
            header (str): Name to assign to the returned filter result column.

        Returns:
            pd.Series: Binary filter results indexed to match ``data``. A value
                of ``1`` indicates that the scan point passes the width filter,
                and ``0`` indicates that it fails.

        Raises:
            KeyError: If one or more required mass or width columns are missing.
            Exception: If an unexpected error occurs during evaluation.
        """
        try:
            arr_widths: np.ndarray = data[
                [f"w_{self.HName}", f"w_{self.SName}", f"w_{self.XName}"]
            ].to_numpy()

            arr_masses: np.ndarray = data[
                [f"m{self.HName}", f"m{self.SName}", f"m{self.XName}"]
            ].to_numpy()

            filt_width: np.ndarray = np.all(
                arr_widths < arr_masses * self.thresholds,
                axis=1,
            )

            return pd.Series(
                filt_width.astype(int),
                index=data.index,
                name=header,
            )

        except KeyError as e:
            logger.error(f"Missing required mass/width columns in DataFrame: {e}")
            raise
        except Exception as e:
            logger.exception(f"Error occurred while applying width filter: {e}")
            raise
