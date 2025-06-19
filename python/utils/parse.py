
# standard libraries
from functools import cached_property
import logging
from typing import Dict, List, Optional, Union

# third-party libraries
import diptest
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import gaussian_kde
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# local modules
from utils.decay_utils import valid_decays
from utils.df_utils import get_df, get_header_string
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point

# class to parse arrays and provide details about data
class Parse:
    """
    Parses and analyzes model scan output data, applying filters, computing observables,
    and providing tools for extracting physics insights such as xb distributions,
    unimodality tests, and optimal points.

    It supports integration with parameter space definitions and model metadata to allow
    for contextual analysis of scalar production and decay behavior.
    """

    def __init__(self,
                 model: Model,
                 file_name: str = ""):
        """
        Initializes the parser with a model and optionally loads scan data from a file.

        Args:
            model (Model): The model used to interpret parameter names and scalar definitions.
            file_name (str, optional): Path to a .tsv file to load immediately (default is empty).
        """

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize model
        self.__model = model

        # initialize class variables
        self.data: pd.DataFrame = pd.DataFrame()

        # get arrays from file name if it is provided
        if file_name:
            self.read_file(file_name)

    @property
    def model(self) -> Model:
        """Returns the associated Model instance used for scalar and parameter definitions."""
        return self.__model

    @cached_property
    def HName(self) -> str:
        """Returns the name of the H scalar defined in the model."""
        return self.model.get_ordered_scalar_name('H')

    @cached_property
    def SName(self) -> str:
        """Returns the name of the S scalar defined in the model."""
        return self.model.get_ordered_scalar_name('S')

    @property
    def filtered_data(self) -> pd.DataFrame:
        """Returns the subset of the data that passes all filters."""
        return self.data.loc[self.filters]

    @property
    def tsv_header(self) -> str:
        """Returns the column header string suitable for .tsv files."""
        return get_header_string(self.data)

    @property
    def input_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Returns a dictionary of input parameter names mapped to their corresponding data arrays."""
        return {name: pd.Series(self.filtered_data[par['fullname']]) for name, par in self.model.input_parameters.items()}

    @property
    def output_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Returns a dictionary of output parameter names mapped to their corresponding data arrays."""
        return {name: pd.Series(self.filtered_data[par['fullname']]) for name, par in self.model.output_parameters.items()}

    @property
    def width_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Returns a dictionary of width parameter names mapped to their corresponding data arrays."""
        return {name: pd.Series(self.filtered_data[par['fullname']]) for name, par in self.model.width_parameters.items()}

    @property
    def parameter_arrays(self) -> Dict[str,pd.Series]:
        """Returns a combined dictionary of input, output, and width parameters."""
        return {**self.input_parameter_arrays, **self.output_parameter_arrays, **self.width_parameter_arrays}

    @property
    def filters(self) -> pd.Series:
        """Returns a boolean Series indicating which rows pass all filtering conditions."""
        return (self.data['filt_width'] * self.data['filt_bounds'] * self.data['filt_signals']).astype(bool)

    @property
    def num_filtered_points(self) -> int:
        """Returns the number of data points that pass all filters."""
        return len(self.filtered_data)

    @property
    def num_unfiltered_points(self) -> int:
        """Returns the total number of data points before filtering."""
        return len(self.data)

    def read_file(self,
                  file_name: str) -> None:
        """
        Loads a .tsv file into the internal data DataFrame.

        Args:
            file_name (str): Path to the .tsv file.
        """
        self.data = get_df(file_name)

    def get_max_xb_point(self,
                         decay: str) -> Point:
        """
        Finds and returns the Point with the maximum xb value for a given decay mode.

        Args:
            decay (str): Name of the decay channel.

        Returns:
            Point: A Point object containing the maximum xb value and corresponding parameters.
        """

        # get xb
        xb = self.get_xb(decay)

        if xb.empty:
            return Point(model=self.model)

        # get index of maximum xsec times BR
        max_idx = xb.idxmax()

        # make dictionary for parameter values for max_xb
        max_xb_par_vals: Dict[str, float] = {par: float(array[max_idx]) for par, array in self.parameter_arrays.items()}

        # return a point object holding xb and other parameters
        return Point(xb = float(xb[max_idx]),
                     model = self.model,
                     par_vals = max_xb_par_vals,
                     tsv_data= self.data.loc[[max_idx]])

    def is_bimodal(self,
                   param_name: str,
                   decay: str,
                   param_space: Optional[ParamSpace] = None) -> bool:
        """
        Performs Hartigan's dip test to check if xb is bimodal with respect to a parameter.

        Args:
            param_name (str): The name of the input parameter.
            decay (str): The decay channel to consider.
            param_space (Optional[ParamSpace]): Optional subspace to restrict the analysis.

        Returns:
            bool: True if the distribution is significantly bimodal, False otherwise.
        """

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
        percentile_threshold = max(percentile_threshold, 0.0)

        # get xb value that corresponds to percentile threshold
        threshold_value = xb.quantile(percentile_threshold)

        # get set of parameter values with xb in selected percentile
        param_selected = self.input_parameter_arrays[param_name][mask][xb > threshold_value]

        # use Hartigan's dip test for unimodality
        result = diptest.diptest(param_selected)
        pval: float = result[1]  # assuming second item is always p-value

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        return pval < pval_threshold

    def get_param_space_splits(self,
                               param_name: str,
                               decay: str,
                               param_space: ParamSpace,
                               min_prominence=0.1,
                               density_threshold=0.01,
                               bw: Union[str, float] = 'silverman',
                               n_points=200) -> List[float]:
        """
        Suggests 1D split points for a parameter column based on:
        - Valleys between peaks in the xb distribution
        - Gaps in the sample density

        Args:
            param_name (str): Parameter to split.
            decay (str): Decay channel.
            param_space (ParamSpace): Parameter subspace to restrict analysis.
            min_prominence (float): Minimum prominence for peak detection in modality analysis.
            density_threshold (float): Density threshold for identifying gaps.
            bw (str or float): Bandwidth method for KDE.
            n_points (int): Number of evaluation points for KDE.

        Returns:
            List[float]: Sorted list of suggested split values for the parameter.
        """

        # get mask for param_space
        mask = self.param_space_mask(param_space)

        data = pd.DataFrame({param_name: self.input_parameter_arrays[param_name][mask],
                     'xb': self.get_xb(decay=decay)[mask]})
        data = data.dropna()
        par_vals = data[param_name].to_numpy(dtype=float)
        xb = data['xb'].to_numpy(dtype=float)

        # ensure a minimum number of points
        if len(par_vals) < 500:
            return []

        # Sort for consistency
        idx = np.argsort(par_vals)
        par_vals_sorted = par_vals[idx]
        xb_sorted = xb[idx]

        # Grid for KDE evaluation
        par_vals_eval: np.ndarray = np.linspace(par_vals_sorted.min(), par_vals_sorted.max(), n_points)

        # Modality-based: KDE weighted by xb
        valley_points = self.get_modality_splits(par_vals=par_vals_sorted,
                                                 xb_vals=xb_sorted,
                                                 par_vals_eval=par_vals_eval,
                                                 bw=bw,
                                                 min_prominence=min_prominence)

        # Density-based: KDE of samples only
        low_density = self.get_density_splits(par_vals=par_vals_sorted,
                                              n_points=n_points,
                                              density_threshold=density_threshold,
                                              bw=bw)

        # Combine, filter duplicates, and sort
        all_splits = np.unique(np.concatenate([valley_points, low_density]))
        return all_splits.tolist()

    def get_modality_splits(self,
                            par_vals: np.ndarray,
                            xb_vals: np.ndarray,
                            par_vals_eval: np.ndarray,
                            bw: Union[str, float] = 'silverman',
                            min_prominence: float = 0.1) -> np.ndarray:
        """
        Identifies valleys between peaks in a KDE weighted by xb to suggest splits.

        Args:
            par_vals (np.ndarray): Sorted parameter values.
            xb_vals (np.ndarray): Corresponding xb values.
            par_vals_eval (np.ndarray): Evaluation grid for KDE.
            bw (str or float): KDE bandwidth method.
            min_prominence (float): Minimum prominence of peaks to detect modes.

        Returns:
            np.ndarray: Array of suggested split points based on modality.
        """

        try:
            kde_xb = gaussian_kde(par_vals, weights=xb_vals, bw_method=bw)
            kde_vals = kde_xb(par_vals_eval)
            peaks, _ = find_peaks(kde_vals, prominence=min_prominence)
            valleys, _ = find_peaks(-kde_vals)
            splits = par_vals_eval[valleys] if len(peaks) > 1 else np.array([], dtype=float)
        except Exception:
            splits = np.array([], dtype=float)
        return splits

    def get_density_splits(self,
                           par_vals: np.ndarray,
                           n_points: int = 200,
                           density_threshold: float = 0.01,
                           bw: Union[str, float] = 'silverman') -> np.ndarray:
        """
        Finds low-density regions in parameter distribution using KDE.

        Args:
            par_vals (np.ndarray): Array of parameter values.
            n_points (int): Number of points in evaluation grid.
            density_threshold (float): Threshold below which a region is considered sparse.
            bw (str or float): KDE bandwidth.

        Returns:
            np.ndarray: Array of midpoints in low-density regions.
        """

        try:
            # Normalize parameter values to [0, 1]
            par_min, par_max = par_vals.min(), par_vals.max()
            par_scaled = (par_vals - par_min) / (par_max - par_min)

            # Evaluate KDE
            kde = gaussian_kde(par_scaled, bw_method=bw)
            x_eval = np.linspace(0, 1, n_points)
            density_vals = kde(x_eval)

            # Find contiguous low-density regions
            below = density_vals < density_threshold
            splits = []
            start_idx = None
            for i, is_low in enumerate(below):
                if is_low and start_idx is None:
                    start_idx = i
                elif not is_low and start_idx is not None:
                    end_idx = i
                    mid_idx = (start_idx + end_idx) // 2
                    mid_x = x_eval[mid_idx]
                    # Map back to original scale
                    splits.append(mid_x * (par_max - par_min) + par_min)
                    start_idx = None
            if start_idx is not None:
                mid_idx = (start_idx + len(x_eval)) // 2
                mid_x = x_eval[mid_idx]
                splits.append(mid_x * (par_max - par_min) + par_min)

            return np.array(splits, dtype=float)

        except Exception as e:
            print(f"[density_splits error] {e}")
            return np.array([], dtype=float)

    def get_2d_density_splits(self,
                            param_x: str,
                            param_y: str,
                            decay: str,
                            param_space: ParamSpace,
                            n_slices: int = 20,
                            min_points_per_slice: int = 100,
                            valley_prominence_threshold: float = 0.2,
                            min_valley_persistence: int = 5,
                            min_valley_width_frac: float = 0.4,
                            n_kde_points: int = 200) -> Dict[str, List[float]]:
        """
        Detects valley-based gaps in a 2D projection by slicing along each axis
        and checking for valleys in the conditional KDE of the other axis.

        Args:
            param_x (str): First parameter.
            param_y (str): Second parameter.
            decay (str): Decay channel to extract xb.
            param_space (ParamSpace): Parameter subspace for restriction.
            n_slices (int): Number of slices to scan along the axis.
            min_points_per_slice (int): Minimum points required to evaluate slice.
            valley_prominence_threshold (float): Relative depth required to consider a dip a valley.
            min_valley_persistence (int): Minimum number of consecutive slices a valley must persist to count.
            n_kde_points (int): Resolution of KDE evaluation.

        Returns:
            Dict[str, List[float]]: Mapping of axis name to list of split locations.
        """
        from scipy.stats import gaussian_kde
        from scipy.signal import argrelextrema
        import numpy as np

        mask = self.param_space_mask(param_space)
        x = self.input_parameter_arrays[param_x][mask]
        y = self.input_parameter_arrays[param_y][mask]
        xb = self.get_xb(decay=decay)[mask]

        data = pd.DataFrame({param_x: x, param_y: y, 'xb': xb}).dropna()
        if len(data) < 500:
            return {}

        def find_valley_transitions(param1_vals, param2_vals) -> List[float]:
            param1_min, param1_max = param1_vals.min(), param1_vals.max()
            bin_edges = np.linspace(param1_min, param1_max, n_slices + 1)
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
            valley_flags = []

            for i in range(n_slices):
                p1_lo, p1_hi = bin_edges[i], bin_edges[i + 1]
                mask = (param1_vals >= p1_lo) & (param1_vals < p1_hi)
                p2_slice = param2_vals[mask]

                if len(p2_slice) < min_points_per_slice:
                    valley_flags.append(False)
                    continue

                kde = gaussian_kde(p2_slice)
                x_eval = np.linspace(p2_slice.min(), p2_slice.max(), n_kde_points)
                y_eval = kde(x_eval)
                valleys = argrelextrema(y_eval, np.less)[0]

                if len(valleys) == 0:
                    valley_flags.append(False)
                    continue

                if (y_eval.max() - y_eval[valleys].min()) > valley_prominence_threshold * y_eval.max():
                    valley_flags.append(True)
                else:
                    valley_flags.append(False)

            # Group persistent valley regions with minimum width
            split_candidates = []
            i = 0
            while i < len(valley_flags):
                if valley_flags[i]:
                    start = i
                    while i < len(valley_flags) and valley_flags[i]:
                        i += 1
                    end = i
                    n_bins = end - start
                    region_width = bin_edges[end] - bin_edges[start]
                    total_width = param1_max - param1_min
                    if n_bins >= min_valley_persistence and region_width >= min_valley_width_frac * total_width:
                        split_center = 0.5 * (bin_centers[start] + bin_centers[end - 1])
                        split_candidates.append(split_center)
                else:
                    i += 1

            return sorted(set(split_candidates))

        x_splits = find_valley_transitions(data[param_x].to_numpy(), data[param_y].to_numpy())
        y_splits = find_valley_transitions(data[param_y].to_numpy(), data[param_x].to_numpy())

        # Prefer the axis with fewer splits (but not 0 vs 1), or first non-empty
        split_dict = {}
        if x_splits and not y_splits:
            split_dict[param_x] = x_splits
        elif y_splits and not x_splits:
            split_dict[param_y] = y_splits
        elif x_splits and y_splits:
            if len(x_splits) <= len(y_splits):
                split_dict[param_x] = x_splits
            else:
                split_dict[param_y] = y_splits

        return split_dict

    def get_xb(self,
               decay: str,
               param_space: Optional[ParamSpace] = None) -> pd.Series:
        """
        Computes the xb = xsec * BR array for a given decay.

        Args:
            decay (str): Decay mode name (or "NoDecay").
            param_space (Optional[ParamSpace]): Optional space to restrict the evaluation.

        Returns:
            pd.Series: xb values over the specified (or full) filtered dataset.
        """

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
        return pd.Series(xb[mask])

    def shrink_param_space_bounds(self,
                                  param_space: ParamSpace,
                                  resolution: float = 0.01) -> None:
        """
        Shrinks parameter bounds in a ParamSpace to match the extent of filtered data within it.

        Args:
            param_space (ParamSpace): Parameter space to update.
            resolution (float): Minimum step size for new bounds.
        """

        filtered_data = self.get_filtered_data(param_space)
        for name, par in self.model.input_parameters.items():
            full_name: str = par['fullname']
            new_min = float(filtered_data[full_name].min())
            new_max = float(filtered_data[full_name].max())
            param_space[name].set_min_max(new_min=new_min,
                                          new_max=new_max,
                                          resolution=resolution)

    def get_filtered_data(self,
                          param_space: Optional[ParamSpace] = None) -> pd.DataFrame:
        """
        Returns filtered data limited to a given parameter space.

        Args:
            param_space (Optional[ParamSpace]): Optional restriction region.

        Returns:
            pd.DataFrame: Filtered data rows inside the parameter space.
        """
        mask = self.param_space_mask(param_space)
        return self.filtered_data.loc[mask]

    def param_space_mask(self,
                         param_space: Optional[ParamSpace] = None) -> pd.Series:
        """
        Returns a boolean mask indicating which filtered data points lie within the given parameter space.

        Args:
            param_space (Optional[ParamSpace]): Region to evaluate inclusion.

        Returns:
            pd.Series: Boolean mask for filtered data.
        """

        df = self.filtered_data
        mask = pd.Series(True, index=df.index)

        # if no param_space is provided, return the mask of all points
        if param_space is None:
            return mask.astype(bool)

        # loop over parameters in the parameter space and create a mask
        for param in param_space:
            col = param.full_name
            mask &= (df[col] > param.low) & (df[col] <= param.high)

        return mask.astype(bool)

    def estimate_effective_volume_by_count(self,
                                           param_space: ParamSpace) -> float:
        """
        Estimates the effective volume of a param_space based on point count,
        assuming uniform random sampling.

        Args:
            param_space (ParamSpace): Region to evaluate.

        Returns:
            float: Proportional effective volume (not normalized unless full volume is known).
        """
        mask = self.param_space_mask(param_space)
        return float(mask.sum())

    def compute_effective_volume(self,
                                 param_space: ParamSpace,
                                 eps: float = 0.05,
                                 min_samples: int = 10) -> float:
        """
        Estimates the effective volume occupied by filtered points in the specified parameter space.
        Uses DBSCAN to identify clusters and computes the sum of 5D convex hull volumes for each.

        Args:
            param_space (ParamSpace): Restrict analysis to this region of parameter space.
            eps (float): Maximum distance between samples for clustering (DBSCAN).
            min_samples (int): Minimum number of samples per cluster (DBSCAN).

        Returns:
            float: Estimated effective volume in N dimensions.
        """

        # Get filtered data in the param space
        df = self.get_filtered_data(param_space)

        # Extract only the 5D input parameters
        param_names = list(self.model.input_parameters.keys())
        cols = [self.model.input_parameters[p]['fullname'] for p in param_names]
        points = df[cols].to_numpy(dtype=float)

        if len(points) <= 5:
            return 0.0

        # Normalize to unit box
        normalized_points = np.empty_like(points)
        for i, param in enumerate(param_names):
            low = param_space[param].low
            high = param_space[param].high
            normalized_points[:, i] = (points[:, i] - low) / (high - low)

        # Cluster the points to identify disconnected components
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(normalized_points)
        labels = clustering.labels_

        # Sum convex hull volumes of each cluster
        total_unit_vol = 0.0
        for label in set(labels):
            if label == -1:
                continue  # skip noise
            cluster_points = normalized_points[labels == label]
            if len(cluster_points) > 5:
                try:
                    hull = ConvexHull(cluster_points)
                    total_unit_vol += hull.volume
                except Exception:
                    continue

        return total_unit_vol * param_space.volume()

    def __get_xsec_prod(self) -> pd.Series:
        """
        Returns the array of production cross-sections for the filtered dataset.

        Specifically retrieves the production cross-section for H3 via gluon-gluon fusion,
        identified by the column 'x_H3_gg'.

        Returns:
            pd.Series: Production cross-section values for each filtered point.
        """
        # TODO: Expand this to use other production modes
        return pd.Series(self.filtered_data['x_H3_gg'])

    def __get_br_decay(self,
                       decay: str) -> pd.Series:
        """
        Computes the total branching ratio (BR) for a specified decay channel.

        Supports a wide range of decay modes involving intermediate particles H and S.
        The returned BR is computed from the product of production and decay subprocesses,
        depending on the channel.

        Args:
            decay (str): The name of the decay mode (e.g., 'SHbbbb', 'Xttbb', etc.).

        Returns:
            pd.Series: Branching ratio values for the specified decay mode.

        Raises:
            ValueError: If the provided decay mode is not recognized or supported.
        """

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
        br_S_tt = self.filtered_data['b_'+self.SName+'_tt']
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

        # ttbb cases
        elif decay == "SttHbb":
            br_decay = br_X_SH * br_S_tt * br_H_bb
        elif decay == "SSttbb":
            br_decay = br_X_SS * br_S_tt * br_S_bb
        elif decay == "Xttbb":
            br1 = br_X_SH * br_S_tt * br_H_bb
            br2 = br_X_SS * br_S_tt * br_S_bb
            br_decay = br1 + br2

        # raise an exception in all other cases
        else:
            raise ValueError(
                f"Unrecognized decay {decay}\n"
                f"Allowed decays are: {', '.join(valid_decays())}."
            )

        # return the decay BR
        return br_decay
