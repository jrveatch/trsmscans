
# standard libraries
from functools import cached_property
import logging
from typing import Dict, Optional

# third-party libraries
import diptest
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt

# local modules
from utils.decay_utils import valid_decays
from utils.df_utils import get_df, get_header_string
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point

# class to parse arrays and provide details about data
class Parse:

    # load new set of arrays
    def __init__(self,
                 model: Model,
                 file_name: str = ""):

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize model
        self.__model = model

        # get arrays from file name if it is provided
        if file_name:
            self.read_file(file_name)

    @property
    def model(self) -> Model:
        """Model object"""
        return self.__model

    @cached_property
    def HName(self) -> str:
        """Name of the H scalar"""
        return self.model.get_ordered_scalar_name('H')

    @cached_property
    def SName(self) -> str:
        """Name of the S scalar"""
        return self.model.get_ordered_scalar_name('S')

    @property
    def filtered_data(self) -> pd.DataFrame:
        return self.data[self.filters]

    @property
    def tsv_header(self) -> str:
        """Header from .tsv file"""
        return get_header_string(self.data)

    @property
    def input_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Dictionary of input parameter arrays"""
        return {name: self.filtered_data[par['fullname']] for name, par in self.model.input_parameters.items()}

    @property
    def output_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Dictionary of output parameter arrays"""
        return {name: self.filtered_data[par['fullname']] for name, par in self.model.output_parameters.items()}

    @property
    def width_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Dictionary of width parameter arrays"""
        return {name: self.filtered_data[par['fullname']] for name, par in self.model.width_parameters.items()}

    @property
    def parameter_arrays(self) -> Dict[str,pd.Series]:
        """Dictionary of parameter arrays"""
        return {**self.input_parameter_arrays, **self.output_parameter_arrays, **self.width_parameter_arrays}

    @property
    def filters(self) -> pd.Series:
        """Filter decisions as a boolean array"""
        return (self.data['filt_width'] * self.data['filt_bounds'] * self.data['filt_signals']).astype(bool)

    @property
    def num_filtered_points(self) -> int:
        """Number of filtered points"""
        return len(self.filtered_data)

    @property
    def num_unfiltered_points(self) -> int:
        """Number of unfiltered points"""
        return len(self.data)

    def read_file(self,
                  file_name: str) -> None:
        """Load new arrays from a .tsv file"""

        # create dataframe object if it does not exist
        if not hasattr(self,"data"):
            self.data = get_df(file_name)

    def get_max_xb_point(self,
                         decay: str) -> Point:
        """Find the point with the highest xb"""

        # get xb
        xb = self.get_xb(decay)

        # get index of maximum xsec times BR
        self.max_idx = xb.idxmax()

        # make dictionary for parameter values for max_xb
        max_xb_par_vals = {par: array[self.max_idx] for par, array in self.parameter_arrays.items()}

        # return a point object holding xb and other parameters
        return Point(xb = xb[self.max_idx],
                     model = self.model,
                     par_vals = max_xb_par_vals)

    def get_min(self,
                par_name: str) -> float:
        """Get the minimum value for a parameter in the data"""
        return self.parameter_arrays[par_name].min()

    def get_max(self,
                par_name: str) -> float:
        """Get the maximum value for a parameter in the data"""
        return self.parameter_arrays[par_name].max()

    def is_bimodal(self,
                   param_name: str,
                   decay: str,
                   param_space: Optional[ParamSpace] = None) -> bool:
        """Check whether xb is unimodal in a parameter"""

        # percentile threshold for xb
        percentile_threshold = 0.98

        # get mask for param_space
        mask = self.param_space_mask(param_space)

        # get xb
        xb = self.get_xb(decay=decay)[mask]

        # number of points available
        num_points = len(xb)

        # minimum number of points for test
        min_points = 200

        # modify percentile threshold to ensure there are at least min_points
        if num_points * (1.0 - percentile_threshold ) < min_points:
            percentile_threshold = 1.0 - min_points/num_points

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # get xb value that corresponds to percentile threshold
        threshold_value = xb.quantile(percentile_threshold)

        # get set of parameter values with xb in selected percentile
        param_selected = self.input_parameter_arrays[param_name][mask][xb > threshold_value]

        # use Hartigan's dip test for unimodality
        _, pval = diptest.diptest(param_selected)

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        return pval < pval_threshold

    def get_multimodal_splits(self,
                              param_name: str,
                              decay: str,
                              param_space: Optional[ParamSpace] = None,
                              min_prominence=0.1,
                              density_threshold=0.01,
                              bw=0.15,
                              n_points=200):
        """
        Suggests 1D split points for a parameter column based on:
        - Valleys between peaks in the xb distribution
        - Gaps in the sample density

        Parameters:
            param_col (str): Name of the parameter to analyze
            value_col (str): Name of the function value column (default 'xb')
            min_prominence (float): Minimum prominence for detecting peaks
            density_threshold (float): Density threshold for detecting gaps
            n_points (int): Resolution of the evaluation grid

        Returns:
            List of split points along the param_col axis
        """

        # get mask for param_space
        mask = self.param_space_mask(param_space)

        data = pd.DataFrame({param_name: self.input_parameter_arrays[param_name][mask],
                     'xb': self.get_xb(decay=decay)[mask]})
        data = data.dropna()
        par_vals = data[param_name].values
        xb = data['xb'].values

        if len(par_vals) < 10:
            return []

        # Sort for consistency
        idx = np.argsort(par_vals)
        par_vals_sorted = par_vals[idx]
        xb_sorted = xb[idx]

        # Grid for KDE evaluation
        par_vals_eval = np.linspace(par_vals_sorted.min(), par_vals_sorted.max(), n_points)

        # KDE (xb-weighted)
        kde_xb = gaussian_kde(par_vals_sorted, weights=xb_sorted, bw_method=bw)
        kde_vals = kde_xb(par_vals_eval)

        # Find peaks and valleys
        peaks, _ = find_peaks(kde_vals, prominence=min_prominence)
        valleys, _ = find_peaks(-kde_vals)

        # Plot
        plt.figure(figsize=(8, 4))
        plt.plot(par_vals_eval, kde_vals, label='KDE(xb-weighted)', color='blue')
        plt.plot(par_vals_eval[peaks], kde_vals[peaks], 'x', label='Peaks', color='green', markersize=10)
        plt.plot(par_vals_eval[valleys], kde_vals[valleys], 'o', label='Valleys', color='red', markersize=8)
        plt.title(f"KDE of xb along {param_name}")
        plt.xlabel(param_name)
        plt.ylabel("Weighted Density")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # Modality-based: KDE weighted by xb
        try:
            kde_xb = gaussian_kde(par_vals_sorted, weights=xb_sorted, bw_method=bw)
            kde_vals = kde_xb(par_vals_eval)
            peaks, _ = find_peaks(kde_vals, prominence=min_prominence)
            valleys, _ = find_peaks(-kde_vals)
            valley_points = par_vals_eval[valleys] if len(peaks) > 1 else []
        except Exception:
            valley_points = []

        # Density-based: KDE of samples only
        try:
            par_vals_scaled = (par_vals_sorted - par_vals_sorted.min()) / (par_vals_sorted.max() - par_vals_sorted.min())
            kde_density = gaussian_kde(par_vals_scaled)
            par_eval_scaled = np.linspace(0, 1, n_points)
            density_vals = kde_density(par_eval_scaled)
            low_density_scaled = par_vals_eval[density_vals < density_threshold]
            low_density = low_density_scaled * (par_vals_sorted.max() - par_vals_sorted.min()) + par_vals_sorted.min()
        except Exception:
            low_density = []

        # Combine, filter duplicates, and sort
        all_splits = np.unique(np.concatenate([valley_points, low_density]))
        return all_splits.tolist()

    def get_xb(self,
               decay: str,
               param_space: Optional[ParamSpace] = None) -> pd.Series:
        """Get array of xb values"""

        # get production cross section
        xsec_prod = self.__get_xsec_prod()

        # if NoDecay is specified, only return production cross-section
        if decay == "NoDecay":
            xb = xsec_prod
        # otherwise include decay BR in xb
        else:
            # get branching ratio
            br_decay = self.__get_br_decay(decay)

            # get total xsec times BR
            xb = xsec_prod * br_decay

        # return total xsec time BR
        mask = self.param_space_mask(param_space)
        return xb[mask]

    def __get_xsec_prod(self) -> pd.Series:
        """Get array of production cross-sections"""
        return self.filtered_data['x_H3_gg'] #* self.filtered_data['b_H3_H1H2']

    def __get_br_decay(self,
                       decay: str) -> pd.Series:
        """Get arrays of decay branching ratios"""

        # BSM BRs
        br_X_SH = self.filtered_data['b_H3_H1H2']
        br_X_SS = self.filtered_data['b_H3_'+self.SName+self.SName]
        br_X_HH = self.filtered_data['b_H3_'+self.HName+self.HName]

        # H SM BRs
        br_H_bb = self.filtered_data['b_'+self.HName+'_bb']
        br_H_tautau = self.filtered_data['b_'+self.HName+'_tautau']
        br_H_WW = self.filtered_data['b_'+self.HName+'_WW']
        br_H_ZZ = self.filtered_data['b_'+self.HName+'_ZZ']
        br_H_gamgam = self.filtered_data['b_'+self.HName+'_gamgam']

        # S SM BRs
        br_S_bb = self.filtered_data['b_'+self.SName+'_bb']
        br_S_tautau = self.filtered_data['b_'+self.SName+'_tautau']
        br_S_WW = self.filtered_data['b_'+self.SName+'_WW']
        br_S_ZZ = self.filtered_data['b_'+self.SName+'_ZZ']
        br_S_gamgam = self.filtered_data['b_'+self.SName+'_gamgam']

        # get appropriate BR for decay mode
        # 4b cases
        if decay == "SHbbbb":
            br_decay = br_X_SH * br_S_bb * br_H_bb
        elif decay == "SSbbbb":
            br_decay = br_X_SS * br_S_bb * br_S_bb
        elif decay == "HHbbbb":
            br_decay = br_X_HH * br_H_bb * br_H_bb
        elif decay == "Xbbbb":
            br1 = br_X_SH * br_S_bb * br_H_bb
            br2 = br_X_SS * br_S_bb * br_S_bb
            br3 = br_X_HH * br_H_bb * br_H_bb
            br_decay = br1 + br2 + br3

        # bbtautau cases
        elif decay == "SbbHtautau":
            br_decay = br_X_SH * br_S_bb * br_H_tautau
        elif decay == "StautauHbb":
            br_decay = br_X_SH * br_S_tautau * br_H_bb
        elif decay == "SHbbtautau":
            br1 = br_X_SH * br_S_bb * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbtautau":
            br_decay = br_X_SS * br_S_bb * br_S_tautau
        elif decay == "HHbbtautau":
            br_decay = br_X_HH * br_H_bb * br_H_tautau
        elif decay == "Xbbtautau":
            br1 = br_X_SH * br_S_bb * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_tautau
            br4 = br_X_HH * br_H_bb * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # bbWW cases
        elif decay == "SbbHWW":
            br_decay = br_X_SH * br_S_bb * br_H_WW
        elif decay == "SWWHbb":
            br_decay = br_X_SH * br_S_WW * br_H_bb
        elif decay == "SHbbWW":
            br1 = br_X_SH * br_S_bb * br_H_WW
            br2 = br_X_SH * br_S_WW * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbWW":
            br_decay = br_X_SS * br_S_bb * br_S_WW
        elif decay == "HHbbWW":
            br_decay = br_X_HH * br_H_bb * br_H_WW
        elif decay == "XbbWW":
            br1 = br_X_SH * br_S_bb * br_H_WW
            br2 = br_X_SH * br_S_WW * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_WW
            br4 = br_X_HH * br_H_bb * br_H_WW
            br_decay = br1 + br2 + br3 + br4

        # bbZZ cases
        elif decay == "SbbHZZ":
            br_decay = br_X_SH * br_S_bb * br_H_ZZ
        elif decay == "SZZHbb":
            br_decay = br_X_SH * br_S_ZZ * br_H_bb
        elif decay == "SHbbZZ":
            br1 = br_X_SH * br_S_bb * br_H_ZZ
            br2 = br_X_SH * br_S_ZZ * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbZZ":
            br_decay = br_X_SS * br_S_bb * br_S_ZZ
        elif decay == "HHbbZZ":
            br_decay = br_X_HH * br_H_bb * br_H_ZZ
        elif decay == "XbbZZ":
            br1 = br_X_SH * br_S_bb * br_H_ZZ
            br2 = br_X_SH * br_S_ZZ * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_ZZ
            br4 = br_X_HH * br_H_bb * br_H_ZZ
            br_decay = br1 + br2 + br3 + br4

        # bbVV cases
        elif decay == "SbbHVV":
            br_decay = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
        elif decay == "SVVHbb":
            br_decay = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
        elif decay == "SHbbVV":
            br1 = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
            br2 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbVV":
            br_decay = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_bb
        elif decay == "HHbbVV":
            br_decay = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_bb
        elif decay == "XbbVV":
            br1 = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
            br2 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
            br3 = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_bb
            br4 = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_bb
            br_decay = br1 + br2 + br3 + br4

        # WWtautau cases
        elif decay == "SWWHtautau":
            br_decay = br_X_SH * br_S_WW * br_H_tautau
        elif decay == "StautauHWW":
            br_decay = br_X_SH * br_S_tautau * br_H_WW
        elif decay == "SHWWtautau":
            br1 = br_X_SH * br_S_WW * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_WW
            br_decay = br1 + br2
        elif decay == "SSWWtautau":
            br_decay = br_X_SS * br_S_WW * br_S_tautau
        elif decay == "HHWWtautau":
            br_decay = br_X_HH * br_H_WW * br_H_tautau
        elif decay == "XWWtautau":
            br1 = br_X_SH * br_S_WW * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_WW
            br3 = br_X_SS * br_S_WW * br_S_tautau
            br4 = br_X_HH * br_H_WW * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # ZZtautau cases
        elif decay == "SZZHtautau":
            br_decay = br_X_SH * br_S_ZZ * br_H_tautau
        elif decay == "StautauHZZ":
            br_decay = br_X_SH * br_S_tautau * br_H_ZZ
        elif decay == "SHZZtautau":
            br1 = br_X_SH * br_S_ZZ * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_ZZ
            br_decay = br1 + br2
        elif decay == "SSZZtautau":
            br_decay = br_X_SS * br_S_ZZ * br_S_tautau
        elif decay == "HHZZtautau":
            br_decay = br_X_HH * br_H_ZZ * br_H_tautau
        elif decay == "XZZtautau":
            br1 = br_X_SH * br_S_ZZ * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_ZZ
            br3 = br_X_SS * br_S_ZZ * br_S_tautau
            br4 = br_X_HH * br_H_ZZ * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # VVtautau cases
        elif decay == "SVVHtautau":
            br_decay = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
        elif decay == "StautauHVV":
            br_decay = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
        elif decay == "SHVVtautau":
            br1 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
            br2 = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
            br_decay = br1 + br2
        elif decay == "SSVVtautau":
            br_decay = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_tautau
        elif decay == "HHVVtautau":
            br_decay = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_tautau
        elif decay == "XVVtautau":
            br1 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
            br2 = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
            br3 = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_tautau
            br4 = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # bbgamgam cases
        elif decay == "SbbHgamgam":
            br_decay = br_X_SH * br_S_bb * br_H_gamgam
        elif decay == "SgamgamHbb":
            br_decay = br_X_SH * br_S_gamgam * br_H_bb
        elif decay == "SHbbgamgam":
            br1 = br_X_SH * br_S_bb * br_H_gamgam
            br2 = br_X_SH * br_S_gamgam * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbgamgam":
            br_decay = br_X_SS * br_S_bb * br_S_gamgam
        elif decay == "HHbbgamgam":
            br_decay = br_X_HH * br_H_bb * br_H_gamgam
        elif decay == "Xbbgamgam":
            br1 = br_X_SH * br_S_bb * br_H_gamgam
            br2 = br_X_SH * br_S_gamgam * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_gamgam
            br4 = br_X_HH * br_H_bb * br_H_gamgam
            br_decay = br1 + br2 + br3 + br4

        # raise an exception in all other cases
        else:
            raise ValueError(
                f"Unrecognized decay {decay}\n"
                f"Allowed decays are: {', '.join(valid_decays())}."
            )

        # return the decay BR
        return br_decay

    def get_filtered_data(self,
                          param_space: Optional[ParamSpace] = None) -> pd.DataFrame:
        """Return a view of filtered_data that is carved out by a parameter space"""
        mask = self.param_space_mask(param_space)
        return self.filtered_data[mask]

    def param_space_mask(self,
                         param_space: Optional[ParamSpace] = None) -> pd.Series:
        """Return a mask of filtered_data that is carved out by a parameter space"""
        df = self.filtered_data
        mask = pd.Series(True, index=df.index)

        # if no param_space is provided, return the mask of all points
        if param_space is None:
            return mask

        # loop over parameters in the parameter space and create a mask
        for param in param_space:
            col = param.full_name
            mask &= (df[col] > param.low) & (df[col] <= param.high)

        return mask

    def write_max_xb_line(self,
                          file_name: str
                         ) -> None:
        """Write line with max xb to a .tsv file"""

        # get max xb row from dataframe
        row = self.data.loc[[self.max_idx]]

        # write it to the summary .tsv
        row.to_csv(file_name,
                   sep='\t',
                   index=True,
                   mode='a',
                   header=False)
